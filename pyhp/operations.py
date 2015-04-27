from pyhp.bytecode import compile_ast
from pyhp.functions import CodeFunction
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

    def __repr__(self):
        return self.__class__.__name__


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
    def __init__(self, body, scope):
        self.body = body
        self.scope = scope

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

        # TODO is there a better way?
        # discard the result if any of the expressions are being called
        # without an assignment operation
        if not isinstance(self.expr, BaseAssignment) \
                or self.expr.has_operation():
            ctx.emit('DISCARD_TOP')


class Function(Node):
    """ A function
    """
    def __init__(self, name, index, body, scope):
        self.identifier = name.get_literal()
        self.index = index
        self.body = body
        self.scope = scope

    def compile(self, ctx):
        body = compile_ast(self.body, self.scope)

        method = CodeFunction(self.identifier, body)

        ctx.emit('LOAD_FUNCTION', method)
        ctx.emit('ASSIGN', self.index, self.identifier)


class Call(Node):
    def __init__(self, left, params):
        self.left = left
        self.params = params

    def compile(self, ctx):
        self.params.compile(ctx)
        self.left.compile(ctx)

        ctx.emit('CALL')


class Identifier(Expression):
    def __init__(self, identifier, index):
        assert index >= 0
        self.identifier = identifier
        self.index = index

    def get_literal(self):
        return self.identifier

    def compile(self, ctx):
        ctx.emit('LOAD_VAR', self.index, self.identifier)


class ArgumentList(ListOp):
    def compile(self, ctx):
        for node in self.nodes:
            node.compile(ctx)
        ctx.emit('LOAD_LIST', len(self.nodes))


class Array(ListOp):
    def compile(self, ctx):
        for element in self.nodes:
            element.compile(ctx)
        ctx.emit('LOAD_ARRAY', len(self.nodes))


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
        ctx.emit('LOAD_MEMBER')


class ConstantInt(Node):
    """ Represent a constant
    """
    def __init__(self, intval):
        self.intval = intval

    def compile(self, ctx):
        ctx.emit('LOAD_INTVAL', self.intval)


class ConstantFloat(Node):
    """ Represent a constant
    """
    def __init__(self, floatval):
        self.floatval = floatval

    def compile(self, ctx):
        ctx.emit('LOAD_FLOATVAL', self.floatval)


class ConstantString(Node):
    """ Represent a constant
    """
    def __init__(self, stringval, variables):
        self.stringval = stringval
        self.variables = variables

    def compile(self, ctx):
        ctx.emit('LOAD_STRINGVAL', self.stringval, self.variables)


class Boolean(Expression):
    def __init__(self, boolval):
        self.bool = boolval

    def compile(self, ctx):
        ctx.emit('LOAD_BOOLEAN', self.bool)


class Null(Expression):
    def compile(self, ctx):
        ctx.emit('LOAD_NULL')


class VariableIdentifier(Expression):
    def __init__(self, identifier, index):
        self.identifier = identifier
        self.index = index

    def get_literal(self):
        return self.identifier

    def compile(self, ctx):
        ctx.emit('LOAD_VAR', self.index, self.identifier)


class Empty(Expression):
    def compile(self, ctx):
        pass


OPERANDS = {
    '+=': 'ADD',
    '-=': 'SUB',
    '++': 'INCR',
    '--': 'DECR',
    '.=': 'ADD',
}

OPERATIONS = unrolling_iterable(OPERANDS.items())


class BaseAssignment(Expression):
    noops = ['=']
    post = False

    def has_operation(self):
        return self.operand not in self.noops

    def compile(self, ctx):
        if self.has_operation():
            self.left.compile(ctx)
            if self.post:
                ctx.emit('DUP')
            self.right.compile(ctx)
            self.compile_operation(ctx)
            if not self.post:
                ctx.emit('DUP')
        else:
            self.right.compile(ctx)

        self.compile_store(ctx)

    def compile_operation(self, ctx):
        # calls to 'emit' have to be very very very static
        op = self.operand
        for key, value in OPERATIONS:
            if op == key:
                ctx.emit(value)
                return
        assert 0

    def compile_store(self, ctx):
        raise NotImplementedError


class AssignmentOperation(BaseAssignment):
    def __init__(self, left, right, operand, post=False):
        self.left = left
        self.index = left.index
        self.right = right
        if self.right is None:
            self.right = Empty()
        self.operand = operand
        self.post = post

    def compile_store(self, ctx):
        ctx.emit('ASSIGN', self.index, self.left.get_literal())


class MemberAssignmentOperation(BaseAssignment):
    def __init__(self, left, right, operand, post=False):
        self.left = left
        self.right = right
        if right is None:
            self.right = Empty()

        self.operand = operand

        self.w_array = self.left.left
        self.expr = self.left.expr
        self.post = post

    def compile_store(self, ctx):
        self.expr.compile(ctx)
        self.w_array.compile(ctx)
        ctx.emit('STORE_MEMBER')


class If(Node):
    """ A very simple if
    """
    def __init__(self, cond, true_branch, else_branch=None):
        self.cond = cond
        self.true_branch = true_branch
        self.else_branch = else_branch

    def compile(self, ctx):
        self.cond.compile(ctx)
        if_opcode = ctx.emit('JUMP_IF_FALSE', 0)
        self.true_branch.compile(ctx)
        true_opcode = ctx.emit('JUMP', 0)
        if_opcode.where = len(ctx)
        if self.else_branch is not None:
            self.else_branch.compile(ctx)
        true_opcode.where = len(ctx)


class WhileBase(Statement):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class While(WhileBase):
    def compile(self, ctx):
        pos = len(ctx)
        self.condition.compile(ctx)
        if_opcode = ctx.emit('JUMP_IF_FALSE', 0)
        self.body.compile(ctx)
        ctx.emit('JUMP', pos)
        if_opcode.where = len(ctx)


class For(Statement):
    def __init__(self, setup, condition, update, body):
        self.setup = setup
        self.condition = condition
        self.update = update
        self.body = body

    def compile(self, ctx):
        self.setup.compile(ctx)
        pos = len(ctx)
        self.condition.compile(ctx)
        if_opcode = ctx.emit('JUMP_IF_FALSE', 0)
        self.body.compile(ctx)
        self.update.compile(ctx)

        # TODO is there a better way?
        # discard the result if any of the expressions are being called
        # without an assignment operation
        if isinstance(self.update, BaseAssignment) \
                and self.update.has_operation():
            ctx.emit('DISCARD_TOP')

        ctx.emit('JUMP', pos)
        if_opcode.where = len(ctx)


class Print(Node):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit('PRINT')


class Return(Statement):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        if self.expr is not None:
            self.expr.compile(ctx)
        ctx.emit('RETURN')


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
            ctx.emit(name)
    BinaryOp.__name__ = name
    return BinaryOp


def create_unary_op(name):
    class UnaryOp(Expression):
        def __init__(self, expr):
            self.expr = expr

        def compile(self, ctx):
            self.expr.compile(ctx)
            ctx.emit(name)
    UnaryOp.__name__ = name
    return UnaryOp

And = create_binary_op('AND')  # +
Or = create_binary_op('OR')  # +

Plus = create_binary_op('ADD')  # +
Mult = create_binary_op('MUL')  # *
Mod = create_binary_op('MOD')  # %
Division = create_binary_op('DIV')  # /
Sub = create_binary_op('SUB')  # -

Eq = create_binary_op('EQ')  # ==
Gt = create_binary_op('GT')  # >
Ge = create_binary_op('GE')  # >=
Lt = create_binary_op('LT')  # <
Le = create_binary_op('LE')  # <=

Not = create_unary_op('NOT')
