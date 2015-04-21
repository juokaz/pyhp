from pyhp import bytecode
from constants import unescapedict
from rpython.rlib.unroll import unrolling_iterable


class Node(object):
    """ The abstract AST node
    """
    def __init__(self):
        pass

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self == other


class Statement(Node):
    pass


class Expression(Statement):
    pass


class ListOp(Expression):
    def __init__(self, nodes):
        self.nodes = nodes


class SourceElements(Statement):
    """
    SourceElements nodes are found on each function declaration and in global
    code
    """
    def __init__(self, func_decl, nodes):
        self.func_decl = func_decl
        self.nodes = nodes

    def compile(self, ctx):
        for funcname, funccode in self.func_decl.items():
            funccode.compile(ctx)

        for node in self.nodes:
            node.compile(ctx)


class Program(Statement):
    def __init__(self, body):
        self.body = body

    def compile(self, ctx):
        self.body.compile(ctx)


class StatementList(Statement):
    def __init__(self, block):
        self.block = block

    def compile(self, ctx):
        self.block.compile(ctx)


class ExprStatement(Node):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)


class FUNCTION(object):
    def __init__(self, name, params, globals=[], body=None):
        assert isinstance(name, str)

        self.name = name
        self.params = params
        self.globals = globals
        self.body = body


class Function(Node):
    """ A function
    """
    def __init__(self, name, params, globals=None, body=None):
        self.name = name.get_literal()
        self.params = params
        self.globals = globals
        self.body = body

    def compile(self, ctx):
        method = FUNCTION(self.name, self.params, self.globals)
        ctx.register_function(method)

        ctx2 = bytecode.CompilerContext()
        ctx2.functions = ctx.functions[:]
        ctx2.function_id = ctx.function_id
        # no variables from the parent context can be accessed
        ctx2.names = []
        ctx2.names_id = {}

        for param in self.params:
            ctx2.register_var(param)

        for variable in self.globals:
            ctx2.register_var(variable)

        if self.body:
            self.body.compile(ctx2)

        method.body = ctx2.create_bytecode()


class Call(Node):
    def __init__(self, left, params):
        self.func = left.get_literal()
        self.params = params

    def compile(self, ctx):
        id, method = ctx.resolve_function(self.func)
        numargs = len(method.params)
        if numargs != len(self.params.nodes):
            raise Exception(
                self.func+' expects %d arguments got %d' %
                (numargs, len(self.params.nodes))
            )

        self.params.compile(ctx)

        ctx.emit(bytecode.CALL, id)


class Identifier(Expression):
    def __init__(self, name):
        self.name = name

    def get_literal(self):
        return self.name


class ArgumentList(ListOp):
    def compile(self, ctx):
        for node in self.nodes:
            node.compile(ctx)
            ctx.emit(bytecode.LOAD_PARAM)


class Array(ListOp):
    def compile(self, ctx):
        for element in self.nodes:
            element.compile(ctx)
        ctx.emit(bytecode.LOAD_ARRAY, len(self.nodes))


class Global(ListOp):
    def compile(self, ctx):
        pass


class Member(Expression):
    "this is for array[name]"
    def __init__(self, left, expr):
        self.left = left
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(bytecode.LOAD_MEMBER)


class ConstantInt(Node):
    """ Represent a constant
    """
    def __init__(self, intval):
        self.intval = intval

    def compile(self, ctx):
        # convert the integer to W_IntObject already here
        from pyhp.interpreter import W_IntObject
        w = W_IntObject(self.intval)
        ctx.emit(bytecode.LOAD_CONSTANT, ctx.register_constant(w))


class ConstantFloat(Node):
    """ Represent a constant
    """
    def __init__(self, floatval):
        self.floatval = floatval

    def compile(self, ctx):
        # convert the float to W_FloatObject already here
        from pyhp.interpreter import W_FloatObject
        w = W_FloatObject(self.floatval)
        ctx.emit(bytecode.LOAD_CONSTANT, ctx.register_constant(w))


class ConstantString(Node):
    """ Represent a constant
    """
    def __init__(self, stringval):
        self.stringval = self.string_unquote(stringval)
        self.variables = self.get_variables(self.stringval)

    def compile(self, ctx):
        for variable in self.variables:
            ctx.emit(bytecode.LOAD_VAR, ctx.get_var(variable))
        # convert the string to W_StringObject already here
        from pyhp.interpreter import W_StringObject
        w = W_StringObject(self.stringval, self.variables)
        ctx.emit(bytecode.LOAD_CONSTANT, ctx.register_constant(w))

    def is_single_quoted(self, string):
        return string[0] == "'"

    def get_variables(self, string):
        # TODO implement this using regular expressions
        variables = [x for x in string.split(' ') if x.startswith('$')]
        return variables

    def string_unquote(self, string):
        # XXX I don't think this works, it's very unlikely IMHO
        #     test it
        temp = []
        stop = len(string)-1
        # XXX proper error
        assert stop >= 0
        last = ""

        internalstring = string[1:stop]

        for c in internalstring:
            if last == "\\":
                # Lookup escape sequence. Ignore the backslash for
                # unknown escape sequences (like SM)
                unescapeseq = unescapedict.get(last+c, c)
                temp.append(unescapeseq)
                c = ' '  # Could be anything
            elif c != "\\":
                temp.append(c)
            last = c
        return ''.join(temp)


class Boolean(Expression):
    def __init__(self, boolval):
        self.bool = boolval

    def compile(self, ctx):
        ctx.emit(bytecode.LOAD_BOOLEAN, self.bool)


class Null(Expression):
    def compile(self, ctx):
        ctx.emit(bytecode.LOAD_NULL)


class VariableIdentifier(Expression):
    def __init__(self, identifier):
        self.identifier = identifier

    def compile(self, ctx):
        ctx.emit(bytecode.LOAD_VAR, ctx.get_var(self.identifier))

    def get_literal(self):
        return self.identifier


class Empty(Expression):
    def compile(self, ctx):
        pass


OPERANDS = {
    '+=': bytecode.ADD,
    '-=': bytecode.SUB,
    '++': bytecode.INCR,
    '--': bytecode.DECR,
}

OPERATIONS = unrolling_iterable(OPERANDS.items())


class BaseAssignment(Expression):
    noops = ['=']

    def has_operation(self):
        return self.operand not in self.noops

    def compile(self, ctx):
        if self.has_operation():
            self.left.compile(ctx)
            self.right.compile(ctx)
            self.compile_operation(ctx)
        else:
            self.right.compile(ctx)

        self.compile_store(ctx)

    def compile_operation(self, ctx):
        # calls to bytecode.emit have to be very very very static
        op = self.operand
        for key, value in OPERATIONS:
            if op == key:
                ctx.emit(value)
                return
        assert 0

    def compile_store(self, ctx):
        raise NotImplementedError


class AssignmentOperation(BaseAssignment):
    def __init__(self, left, right, operand):
        self.left = left
        self.identifier = left.get_literal()
        self.right = right
        if self.right is None:
            self.right = Empty()
        self.operand = operand

    def compile_store(self, ctx):
        ctx.emit(bytecode.ASSIGN, ctx.register_var(self.identifier))


class MemberAssignmentOperation(BaseAssignment):
    def __init__(self, left, right, operand):
        self.left = left
        self.right = right
        if right is None:
            self.right = Empty()

        self.operand = operand

        self.w_array = self.left.left
        self.expr = self.left.expr

    def compile_store(self, ctx):
        self.expr.compile(ctx)
        self.w_array.compile(ctx)
        ctx.emit(bytecode.STORE_MEMBER)


class If(Node):
    """ A very simple if
    """
    def __init__(self, cond, true_branch, else_branch=None):
        self.cond = cond
        self.true_branch = true_branch
        self.else_branch = else_branch

    def compile(self, ctx):
        self.cond.compile(ctx)
        ctx.emit(bytecode.JUMP_IF_FALSE, 0)
        jmp_pos = len(ctx.data) - 1
        self.true_branch.compile(ctx)
        ctx.data[jmp_pos] = chr(len(ctx.data))


class WhileBase(Statement):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class While(WhileBase):
    def compile(self, ctx):
        pos = len(ctx.data)
        self.condition.compile(ctx)
        ctx.emit(bytecode.JUMP_IF_FALSE, 0)
        jmp_pos = len(ctx.data) - 1
        self.body.compile(ctx)
        ctx.emit(bytecode.JUMP_BACKWARD, pos)
        ctx.data[jmp_pos] = chr(len(ctx.data))


class Print(Node):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(bytecode.PRINT)


class Return(Statement):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        if self.expr is not None:
            self.expr.compile(ctx)
        ctx.emit(bytecode.RETURN)


class Block(Statement):
    def __init__(self, nodes):
        self.nodes = nodes

    def compile(self, ctx):
        for node in self.nodes:
            node.compile(ctx)


def create_binary_op(name):
    class BinaryOp(Expression):
        def __init__(self, left, right):
            self.left = left
            self.right = right

        def compile(self, ctx):
            self.left.compile(ctx)
            self.right.compile(ctx)
            b_name = 'BINARY_%s' % name.upper()
            ctx.emit(bytecode.BytecodesMap[b_name])
    BinaryOp.__name__ = name
    return BinaryOp

Plus = create_binary_op('ADD')  # +
Mult = create_binary_op('MUL')  # *
Mod = create_binary_op('MOD')  # %
Division = create_binary_op('DIV')  # /
Sub = create_binary_op('SUB')  # -

Eq = create_binary_op('EQ')  # ==
Ge = create_binary_op('GE')  # >=
Lt = create_binary_op('LT')  # <

StringJoin = create_binary_op('STRINGJOIN')  # .
