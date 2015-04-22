import py
from rpython.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function
from rpython.rlib.parsing.parsing import ParseError
from rpython.rlib.parsing.tree import RPythonVisitor, Symbol
from rpython.rlib.rarithmetic import ovfcheck_float_to_int
from pyhp import pyhpdir
from pyhp import operations

grammar_file = 'grammar.txt'
grammar = py.path.local(pyhpdir).join(grammar_file).read("rt")
try:
    regexs, rules, ToAST = parse_ebnf(grammar)
except ParseError, e:
    print e.nice_error_message(filename=grammar_file, source=grammar)
    raise
_parse = make_parse_function(regexs, rules, eof=True)


class SymbolsMap(object):
    def __init__(self):
        self.symbols = []
        self.symbols_id = {}

    def add(self, name):
        if name not in self.symbols_id:
            self.symbols_id[name] = len(self.symbols)
            self.symbols.append(name)
            idx = len(self.symbols) - 1
        else:
            idx = self.symbols_id[name]

        assert isinstance(idx, int)
        assert idx >= 0
        return idx

    def get_index(self, name):
        return self.symbols_id[name]

    def get_name(self, index):
        return self.symbols[index]


class Scope(object):
    def __init__(self, symbols_map):
        self.symbols = symbols_map
        self.functions = []
        self.variables = []
        self.globals = []

    def add_symbol(self, name):
        return self.symbols.add(name)

    def add_variable(self, name):
        idx = self.add_symbol(name)

        self.variables.append(name)
        return idx

    def add_global(self, name):
        idx = self.add_symbol(name)

        self.globals.append(name)
        return idx

    def add_function(self, name):
        idx = self.add_symbol(name)

        self.functions.append(name)
        return idx

    def finalize(self):
        return FinalScope(self.symbols, self.functions, self.variables,
                          self.globals)


class FinalScope(object):
    _immutable_fields_ = ['symbols', 'functions[*]', 'variables[*]',
                          'globals[*]']

    def __init__(self, symbols, functions, variables, globals):
        self.symbols = symbols
        self.functions = functions[:]
        self.variables = variables[:]
        self.globals = globals[:]

    def get_index(self, name):
        return self.symbols.get_index(name)

    def get_name(self, name):
        return self.symbols.get_name(name)

    def get_symbols(self):
        return self.symbols

    def len(self):
        return len(self.symbols)


class FakeParseError(Exception):
    def __init__(self, msg):
        self.msg = msg


class Transformer(RPythonVisitor):
    """ Transforms AST from the obscure format given to us by the ennfparser
    to something easier to work with
    """
    BINOP_TO_CLS = {
        '+': operations.Plus,
        '-': operations.Sub,
        '*': operations.Mult,
        '/': operations.Division,
        '%': operations.Mod,
        '>': operations.Gt,
        '>=': operations.Ge,
        '<': operations.Lt,
        '<=': operations.Le,
        '.': operations.Plus,
        '&&': operations.And,
        '||': operations.Or,
        '==': operations.Eq,
        '[': operations.Member,
    }

    def __init__(self):
        # one symbols map per whole application to avoid index colisions
        self.root_symbols_map = SymbolsMap()
        self.funclists = []
        self.scopes = []
        self.depth = -1

    def visit_main(self, node):
        self.enter_scope()
        body = self.dispatch(node.children[0])
        scope = self.current_scope()
        final_scope = scope.finalize()
        return operations.Program(body, final_scope)

    def visit_arguments(self, node):
        nodes = [self.dispatch(child) for child in node.children[1:]]
        return operations.ArgumentList(nodes)

    def visit_sourceelements(self, node):
        self.funclists.append({})
        nodes = []
        for child in node.children:
            node = self.dispatch(child)
            if node is None:
                continue

            if isinstance(node, operations.Global):
                for node in node.nodes:
                    self.declare_global(node.get_literal())
                continue

            nodes.append(node)

        func_decl = self.funclists.pop()
        return operations.SourceElements(func_decl, nodes)

    def functioncommon(self, node, declaration=True):
        self.enter_scope()

        i = 0
        identifier, i = self.get_next_expr(node, i)

        p = []
        parameters, i = self.get_next_expr(node, i)
        if parameters is not None:
            p = [pident.get_literal() for pident in parameters.nodes]

        functionbody, i = self.get_next_expr(node, i)

        scope = self.current_scope()
        final_scope = scope.finalize()

        self.exit_scope()

        funcindex = -1
        if declaration:
            funcindex = self.declare_symbol(identifier.get_literal())

        funcobj = operations.Function(identifier, funcindex, p, functionbody,
                                      final_scope)

        if declaration:
            self.declare_function(identifier.get_literal(), funcobj)

        return funcobj

    def visit_functiondeclaration(self, node):
        self.functioncommon(node)
        return None

    def visit_formalparameterlist(self, node):
        nodes = [self.dispatch(child) for child in node.children]
        return operations.ArgumentList(nodes)

    def visit_statementlist(self, node):
        block = self.dispatch(node.children[0])
        return operations.StatementList(block)

    def binaryop(self, node):
        left = self.dispatch(node.children[0])
        for i in range((len(node.children) - 1) // 2):
            op = node.children[i * 2 + 1]
            right = self.dispatch(node.children[i * 2 + 2])
            result = self.BINOP_TO_CLS[op.additional_info](left, right)
            left = result
        return left
    visit_logicalorexpression = binaryop
    visit_logicalandexpression = binaryop
    visit_stringjoinexpression = binaryop
    visit_relationalexpression = binaryop
    visit_equalityexpression = binaryop
    visit_additiveexpression = binaryop
    visit_multiplicativeexpression = binaryop
    visit_expression = binaryop
    visit_memberexpression = binaryop

    def literalop(self, node):
        value = node.children[0].additional_info
        if value == "true":
            return operations.Boolean(True)
        elif value == "false":
            return operations.Boolean(False)
        else:
            return operations.Null()
    visit_nullliteral = literalop
    visit_booleanliteral = literalop

    def visit_numericliteral(self, node):
        number = ""
        for node in node.children:
            number += node.additional_info
        try:
            f = float(number)
            i = ovfcheck_float_to_int(f)
            if i != f:
                return operations.ConstantFloat(f)
            else:
                return operations.ConstantInt(i)
        except (ValueError, OverflowError):
            return operations.ConstantFloat(float(node.additional_info))

    def visit_expressionstatement(self, node):
        return operations.ExprStatement(self.dispatch(node.children[0]))

    def visit_printstatement(self, node):
        return operations.Print(self.dispatch(node.children[1]))

    def visit_globalstatement(self, node):
        nodes = [self.dispatch(child) for child in node.children[1].children]
        return operations.Global(nodes)

    def visit_callexpression(self, node):
        left = self.dispatch(node.children[0])
        nodelist = node.children[1:]
        while nodelist:
            currnode = nodelist.pop(0)
            if isinstance(currnode, Symbol):
                raise NotImplementedError("Not implemented")
            else:
                right = self.dispatch(currnode)
                left = operations.Call(left, right)

        return left

    def _dispatch_assignment(self, left, atype, prepost):
        if self.is_variable(left):
            return operations.AssignmentOperation(left, None, atype)
        elif self.is_member(left):
            return operations.MemberAssignmentOperation(left, None, atype)
        else:
            raise FakeParseError("invalid lefthand expression")

    def visit_postfixexpression(self, node):
        op = node.children[1]
        child = self.dispatch(node.children[0])
        # all postfix expressions are assignments
        return self._dispatch_assignment(child, op.additional_info, 'post')

    def visit_arrayliteral(self, node):
        l = [self.dispatch(child) for child in node.children[1:]]
        return operations.Array(l)

    def visit_block(self, node):
        l = [self.dispatch(child) for child in node.children[1:]]
        return operations.Block(l)

    def visit_assignmentexpression(self, node):
        left = self.dispatch(node.children[0])
        operation = node.children[1].additional_info
        right = self.dispatch(node.children[2])

        if self.is_variable(left):
            return operations.AssignmentOperation(left, right, operation)
        elif self.is_member(left):
            return operations.MemberAssignmentOperation(left, right, operation)
        else:
            raise FakeParseError("invalid lefthand expression")

    def visit_ifstatement(self, node):
        condition = self.dispatch(node.children[0])
        ifblock = self.dispatch(node.children[1])
        if len(node.children) > 2:
            elseblock = self.dispatch(node.children[2])
        else:
            elseblock = None
        return operations.If(condition, ifblock, elseblock)

    def visit_conditionalexpression(self, node):
        condition = self.dispatch(node.children[0])
        truepart = self.dispatch(node.children[2])
        falsepart = self.dispatch(node.children[3])
        return operations.If(condition, truepart, falsepart)

    def visit_iterationstatement(self, node):
        return self.dispatch(node.children[0])

    def visit_whiles(self, node):
        itertype = node.children[0].additional_info
        if itertype == 'while':
            condition = self.dispatch(node.children[1])
            block = self.dispatch(node.children[2])
            return operations.While(condition, block)
        else:
            raise NotImplementedError("Unknown while version %s" % (itertype,))

    def visit_regularfor(self, node):
        i = 1
        setup, i = self.get_next_expr(node, i)
        condition, i = self.get_next_expr(node, i)
        if isinstance(condition, operations.Null):
            condition = operations.Boolean(True)
        update, i = self.get_next_expr(node, i)
        body, i = self.get_next_expr(node, i)

        if setup is None:
            setup = operations.Empty()
        if condition is None:
            condition = operations.Boolean(True)
        if update is None:
            update = operations.Empty()
        if body is None:
            body = operations.Empty()

        return operations.For(setup, condition, update, body)

    def visit_returnstatement(self, node):
        if len(node.children) > 0:
            value = self.dispatch(node.children[0])
        else:
            value = None
        return operations.Return(value)

    def visit_IDENTIFIERNAME(self, node):
        name = node.additional_info
        index = self.declare_symbol(name)
        return operations.Identifier(name, index)

    def visit_VARIABLENAME(self, node):
        name = node.additional_info
        index = self.declare_variable(name)
        return operations.VariableIdentifier(name, index)

    def string(self, node):
        return operations.ConstantString(node.additional_info)
    visit_DOUBLESTRING = string
    visit_SINGLESTRING = string

    def get_next_expr(self, node, i):
        if isinstance(node.children[i], Symbol) and \
           node.children[i].additional_info in [';', ')', '(', '}']:
            return None, i+1
        else:
            return self.dispatch(node.children[i]), i+2

    def is_variable(self, obj):
        from pyhp.operations import VariableIdentifier
        return isinstance(obj, VariableIdentifier)

    def is_member(self, obj):
        from pyhp.operations import Member
        return isinstance(obj, Member)

    def enter_scope(self):
        self.depth = self.depth + 1

        new_scope = Scope(self.root_symbols_map)
        self.scopes.append(new_scope)

    def declare_symbol(self, symbol):
        s = symbol
        idx = self.scopes[-1].add_symbol(s)
        return idx

    def declare_variable(self, symbol):
        s = symbol
        idx = self.scopes[-1].add_variable(s)
        return idx

    def declare_global(self, symbol):
        s = symbol
        idx = self.scopes[-1].add_global(s)
        return idx

    def declare_function(self, symbol, funcobj):
        s = symbol
        self.funclists[-1][s] = funcobj
        idx = self.scopes[-1].add_function(s)
        return idx

    def exit_scope(self):
        self.depth = self.depth - 1
        self.scopes.pop()

    def current_scope(self):
        try:
            return self.scopes[-1]
        except IndexError:
            return None
