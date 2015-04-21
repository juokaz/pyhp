import py
from rpython.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function
from rpython.rlib.parsing.tree import RPythonVisitor, Symbol
from rpython.rlib.parsing.parsing import ParseError
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


class Scope(object):
    def __init__(self):
        self.local_variables = []

    def __repr__(self):
        return 'Scope ' + repr(self.local_variables)

    def add_local(self, variable):
        if not self.is_local(variable) is True:
            self.local_variables.append(variable)

    def is_local(self, variable):
        return variable in self.local_variables

    def get_local(self, variable):
        return self.local_variables.index(variable)


class Scopes(object):
    def __init__(self):
        self.scopes = []

    def current_scope(self):
        if not self.scopes:
            return None
        else:
            return self.scopes[-1]

    def new_scope(self):
        self.scopes.append(Scope())

    def end_scope(self):
        self.scopes.pop()

    def variables(self):
        if self.scope_present():
            return self.current_scope().local_variables
        return []

    def is_local(self, variable):
        return self.scope_present() is True \
            and self.current_scope().is_local(variable) is True

    def scope_present(self):
        return self.current_scope() is not None

    def add_local(self, variable):
        if self.scope_present():
            self.current_scope().add_local(variable)

    def get_local(self, variable):
        return self.current_scope().get_local(variable)


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
        '>=': operations.Ge,
        '==': operations.Eq,
        '<': operations.Lt,
        '.': operations.StringJoin,
        '[': operations.Member,
    }

    def __init__(self):
        self.varlists = []
        self.funclists = []
        self.scopes = Scopes()

    def visit_main(self, node):
        body = self.dispatch(node.children[0])
        return operations.Program(body)

    def visit_arguments(self, node):
        nodes = [self.dispatch(child) for child in node.children[1:]]
        return operations.ArgumentList(nodes)

    def visit_sourceelements(self, node):
        self.varlists.append({})
        self.funclists.append({})
        nodes = []
        for child in node.children:
            node = self.dispatch(child)
            if node is not None:
                nodes.append(node)
        func_decl = self.funclists.pop()
        return operations.SourceElements(func_decl, nodes)

    def functioncommon(self, node, declaration=True):
        self.scopes.new_scope()
        i = 0
        identifier, i = self.get_next_expr(node, i)

        p = []
        parameters, i = self.get_next_expr(node, i)
        if parameters is not None:
            p = [pident.get_literal() for pident in parameters.nodes]

        functionbody, i = self.get_next_expr(node, i)

        global_variables = None
        if functionbody:
            for node in functionbody.nodes:
                if isinstance(node, operations.Global):
                    global_variables = node

        g = []
        if global_variables is not None:
            g = [pident.get_literal() for pident in global_variables.nodes]

        funcobj = operations.Function(identifier, p, g, functionbody)
        if declaration:
            self.funclists[-1][identifier.get_literal()] = funcobj
        self.scopes.end_scope()
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
    visit_stringjoinexpression = binaryop
    visit_relationalexpression = binaryop
    visit_equalityexpression = binaryop
    visit_additiveexpression = binaryop
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

    def visit_returnstatement(self, node):
        if len(node.children) > 0:
            value = self.dispatch(node.children[0])
        else:
            value = None
        return operations.Return(value)

    def visit_DECIMALLITERAL(self, node):
        try:

            f = float(node.additional_info)
            i = ovfcheck_float_to_int(f)
            if i != f:
                return operations.ConstantFloat(f)
            else:
                return operations.ConstantInt(i)
        except (ValueError, OverflowError):
            return operations.ConstantFloat(float(node.additional_info))

    def visit_IDENTIFIERNAME(self, node):
        name = node.additional_info
        return operations.Identifier(name)

    def visit_VARIABLENAME(self, node):
        name = node.additional_info
        return operations.VariableIdentifier(name)

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


transformer = Transformer()


def parse(source):
    """ Parse the source code and produce an AST
    """
    try:
        t = _parse(source)
    except ParseError, e:
        print e.nice_error_message(source=source)
        raise
    ast = ToAST().transform(t)
    return transformer.dispatch(ast)
