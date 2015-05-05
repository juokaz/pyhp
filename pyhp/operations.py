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

        if len(self.nodes) > 1:
            for node in self.nodes[:-1]:
                node.compile(ctx)
                ctx.emit('DISCARD_TOP')

        if len(self.nodes) > 0:
            node = self.nodes[-1]
            node.compile(ctx)
        else:
            ctx.emit('LOAD_UNDEFINED')


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


class Function(Node):
    """ A function
    """
    def __init__(self, name, body, scope):
        self.identifier = name.get_literal()
        self.body = body
        self.scope = scope

    def compile(self, ctx):
        body = compile_ast(self.body, self.scope)

        method = CodeFunction(self.identifier, body)

        ctx.emit('DECLARE_FUNCTION', self.identifier, method)


class Call(Node):
    def __init__(self, left, params):
        self.left = left
        self.params = params

    def compile(self, ctx):
        self.params.compile(ctx)
        self.left.compile(ctx)

        ctx.emit('CALL')


class Identifier(Expression):
    def __init__(self, identifier):
        self.identifier = identifier

    def get_literal(self):
        return self.identifier

    def compile(self, ctx):
        ctx.emit('LOAD_FUNCTION', self.identifier)


class Constant(Expression):
    def __init__(self, identifier):
        self.identifier = identifier

    def compile(self, ctx):
        ctx.emit('LOAD_CONSTANT', self.identifier)


class ArgumentList(ListOp):
    def compile(self, ctx):
        for node in self.nodes:
            if isinstance(node, VariableIdentifier):
                ctx.emit('LOAD_REF', node.index, node.identifier)
            else:
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
        if isinstance(self.left, VariableIdentifier):
            ctx.emit('LOAD_MEMBER_VAR', self.left.index, self.left.identifier)
        else:
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


class EmptyExpression(Expression):
    def compile(self, ctx):
        ctx.emit('LOAD_UNDEFINED')


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
        else:
            self.right.compile(ctx)

        self.compile_store(ctx)

        if self.post:
            ctx.emit('DISCARD_TOP')

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


class Unconditional(Statement):
    def __init__(self, count):
        self.count = count


class Break(Unconditional):
    def compile(self, ctx):
        assert self.count is None
        ctx.emit('LOAD_UNDEFINED')
        ctx.emit_break()


class Continue(Unconditional):
    def compile(self, ctx):
        assert self.count is None
        ctx.emit('LOAD_UNDEFINED')
        ctx.emit_continue()


class If(Node):
    """ A very simple if
    """
    def __init__(self, cond, true_branch, else_branch=None):
        self.cond = cond
        self.true_branch = true_branch
        self.else_branch = else_branch

    def compile(self, ctx):
        self.cond.compile(ctx)
        endif = ctx.prealocate_label()
        endthen = ctx.prealocate_label()
        ctx.emit('JUMP_IF_FALSE', endthen)
        self.true_branch.compile(ctx)
        ctx.emit('JUMP', endif)
        ctx.emit_label(endthen)

        if self.else_branch is not None:
            self.else_branch.compile(ctx)
        else:
            ctx.emit('LOAD_UNDEFINED')

        ctx.emit_label(endif)


class WhileBase(Statement):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class While(WhileBase):
    def compile(self, ctx):
        ctx.emit('LOAD_UNDEFINED')
        startlabel = ctx.emit_startloop_label()
        ctx.continue_at_label(startlabel)

        self.condition.compile(ctx)

        endlabel = ctx.prealocate_endloop_label()
        ctx.emit('JUMP_IF_FALSE', endlabel)

        self.body.compile(ctx)
        ctx.emit('DISCARD_TOP')

        ctx.emit('JUMP', startlabel)
        ctx.emit_endloop_label(endlabel)
        ctx.done_continue()


class For(Statement):
    def __init__(self, setup, condition, update, body):
        self.setup = setup
        self.condition = condition
        self.update = update
        self.body = body

    def compile(self, ctx):
        self.setup.compile(ctx)
        ctx.emit('DISCARD_TOP')

        ctx.emit('LOAD_UNDEFINED')

        startlabel = ctx.emit_startloop_label()
        endlabel = ctx.prealocate_endloop_label()
        update = ctx.prealocate_updateloop_label()

        self.condition.compile(ctx)
        ctx.emit('JUMP_IF_FALSE', endlabel)
        ctx.emit('DISCARD_TOP')

        self.body.compile(ctx)

        ctx.emit_updateloop_label(update)
        self.update.compile(ctx)
        ctx.emit('DISCARD_TOP')

        ctx.emit('JUMP', startlabel)
        ctx.emit_endloop_label(endlabel)


class Foreach(Statement):
    def __init__(self, lobject, key, variable, body):
        self.w_object = lobject
        self.key = key
        self.variable = variable
        self.body = body

    def compile(self, ctx):
        w_object = self.w_object
        key = self.key
        variable = self.variable
        body = self.body

        w_object.compile(ctx)
        ctx.emit('LOAD_ITERATOR')
        # load the "last" iterations result
        ctx.emit('LOAD_UNDEFINED')
        precond = ctx.emit_startloop_label()
        finish = ctx.prealocate_endloop_label(True)

        ctx.emit('JUMP_IF_ITERATOR_EMPTY', finish)

        # put the next iterator value onto stack
        ctx.emit('NEXT_ITERATOR')

        # store iterator key into appropriate place
        if key is None:
            ctx.emit('DISCARD_TOP')
        elif isinstance(key, VariableIdentifier):
            name = key.identifier
            index = key.index
            ctx.emit('ASSIGN', index, name)
            ctx.emit('DISCARD_TOP')
        else:
            raise Exception(u'unsupported')

        # store iterator value into appropriate place
        if isinstance(variable, VariableIdentifier):
            name = variable.identifier
            index = variable.index
            ctx.emit('ASSIGN', index, name)
            ctx.emit('DISCARD_TOP')
        else:
            raise Exception(u'unsupported')

        body.compile(ctx)
        ctx.emit('JUMP', precond)
        ctx.emit_endloop_label(finish)


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
        if self.expr is None:
            ctx.emit('LOAD_UNDEFINED')
        else:
            self.expr.compile(ctx)
        ctx.emit('RETURN')


class Block(Statement):
    def __init__(self, nodes):
        self.nodes = nodes

    def compile(self, ctx):
        if len(self.nodes) > 1:
            for node in self.nodes[:-1]:
                node.compile(ctx)
                ctx.emit('DISCARD_TOP')

        if len(self.nodes) > 0:
            node = self.nodes[-1]
            node.compile(ctx)
        else:
            ctx.emit('LOAD_UNDEFINED')


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


class And(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.left.compile(ctx)
        one = ctx.prealocate_label()
        ctx.emit('JUMP_IF_FALSE_NOPOP', one)
        self.right.compile(ctx)
        ctx.emit_label(one)


class Or(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.left.compile(ctx)
        one = ctx.prealocate_label()
        ctx.emit('JUMP_IF_TRUE_NOPOP', one)
        self.right.compile(ctx)
        ctx.emit_label(one)

Comma = create_binary_op('COMMA')

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

Ursh = create_binary_op('URSH')  # >>>
Rsh = create_binary_op('RSH')  # >>
Lsh = create_binary_op('LSH')  # <<

Not = create_unary_op('NOT')
