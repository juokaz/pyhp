from pyhp.bytecode import compile_ast
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib.objectmodel import enforceargs


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

    def __str__(self):
        return self.str()

    def str(self):
        return unicode(self.__class__.__name__)

    def _indent(self, block):
        return u"\n".join([u"\t" + line for line in block])

    def _indent_block(self, block):
        return self._indent(block.str().split(u"\n"))


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
            ctx.emit('LOAD_NULL')

        if self.nodes and not isinstance(self.nodes[-1], Return):
            ctx.emit('RETURN')

    def str(self):
        string = []
        for node in self.func_decl.values():
            for line in node.str().split(u"\n"):
                string.append(line)
        for node in self.nodes:
            for line in node.str().split(u"\n"):
                string.append(line)
        body = self._indent(string)
        return u'SourceElements (\n%s\n)' % body


class Program(Statement):
    def __init__(self, body, scope):
        self.body = body
        self.scope = scope

    def compile(self, ctx):
        self.body.compile(ctx)

    def str(self):
        body = self._indent_block(self.body)
        return u'Program (\n%s\n)' % body


class ExprStatement(Node):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)

    def str(self):
        return u'ExprStatement (%s)' % self.expr.str()


class Function(Node):
    """ A function
    """
    def __init__(self, name, body, scope):
        self.identifier = name.get_literal()
        if body is None:
            body = Return(None)
        self.body = body
        self.scope = scope

    def compile(self, ctx):
        body = self.body
        body = compile_ast(body, self.scope, self.identifier)

        ctx.emit('DECLARE_FUNCTION', self.identifier, body)

    def str(self):
        body = self._indent_block(self.body)
        return u'Function (%s,\n%s\n)' % (self.identifier, body)


class Call(Node):
    def __init__(self, left, params):
        self.left = left
        self.params = params

    def compile(self, ctx):
        self.params.compile(ctx)
        self.left.compile(ctx)

        ctx.emit('CALL', len(self.params.nodes))

    def str(self):
        return u'Call (%s, %s)' % (self.left.str(), self.params.str())


class Identifier(Expression):
    def __init__(self, identifier):
        self.identifier = identifier

    def get_literal(self):
        return self.identifier

    def compile(self, ctx):
        ctx.emit('LOAD_FUNCTION', self.identifier)

    def str(self):
        return u'Identifier %s' % self.identifier


class Constant(Expression):
    def __init__(self, identifier):
        self.identifier = identifier

    def compile(self, ctx):
        ctx.emit('LOAD_CONSTANT', self.identifier)

    def str(self):
        return u'Constant (%s)' % self.identifier


class ArgumentList(ListOp):
    def compile(self, ctx):
        for node in self.nodes:
            if isinstance(node, VariableIdentifier):
                ctx.emit('LOAD_REF', node.index, node.identifier)
            else:
                node.compile(ctx)

    def str(self):
        arguments = u", ".join([node.str() for node in self.nodes])
        return u'ArgumentList (%s)' % arguments


class Array(ListOp):
    def compile(self, ctx):
        for element in self.nodes:
            element.compile(ctx)
        ctx.emit('LOAD_ARRAY', len(self.nodes))

    def str(self):
        array = u", ".join([node.str() for node in self.nodes])
        return u'Array (%s)' % array


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

    def str(self):
        return u'Member (%s, %s)' % (self.left.str(), self.expr.str())


class ConstantInt(Node):
    """ Represent a constant
    """
    def __init__(self, intval):
        self.intval = intval

    def compile(self, ctx):
        ctx.emit('LOAD_INTVAL', self.intval)

    def str(self):
        return u'ConstantInt %d' % self.intval


class ConstantFloat(Node):
    """ Represent a constant
    """
    def __init__(self, floatval):
        self.floatval = floatval

    def compile(self, ctx):
        ctx.emit('LOAD_FLOATVAL', self.floatval)

    def str(self):
        return u'ConstantFloat %s' % unicode(str(self.floatval))


class ConstantString(Node):
    """ Represent a constant
    """
    @enforceargs(None, unicode)
    def __init__(self, stringval):
        self.stringval = stringval

    def compile(self, ctx):
        ctx.emit('LOAD_STRINGVAL', self.stringval)

    def str(self):
        return u'ConstantString "%s"' % self.stringval


class StringSubstitution(Node):
    """ Represent a constant
    """
    def __init__(self, strings):
        self.strings = strings

    def compile(self, ctx):
        for part in self.strings:
            part.compile(ctx)
        ctx.emit('LOAD_STRING_SUBSTITUTION', len(self.strings))

    def str(self):
        strings = u", ".join([node.str() for node in self.strings])
        return u'StringSubstitution (%s)' % strings


class Boolean(Expression):
    def __init__(self, boolval):
        self.bool = boolval

    def compile(self, ctx):
        ctx.emit('LOAD_BOOLEAN', self.bool)

    def str(self):
        return u'Boolean %s' % unicode(str(self.bool))


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

    def str(self):
        return u'VariableIdentifier (%d, %s)' % (self.index, self.identifier)


class Empty(Expression):
    def compile(self, ctx):
        pass


class EmptyExpression(Expression):
    def compile(self, ctx):
        ctx.emit('LOAD_NULL')


OPERANDS = {
    '+=': 'ADD',
    '-=': 'SUB',
    '++': 'INCR',
    '--': 'DECR',
    '.=': 'ADD',
}

OPERATIONS = unrolling_iterable(OPERANDS.items())


class BaseAssignment(Expression):
    post = False

    def has_operation(self):
        return self.operand != '='

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

    def str(self):
        return u'AssignmentOperation (%s, %s, %s)' % (self.left.str(),
                                                      unicode(self.operand),
                                                      self.right.str())


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

        if isinstance(self.w_array, VariableIdentifier):
            ctx.emit('STORE_MEMBER_VAR', self.w_array.index,
                     self.w_array.identifier)
        else:
            self.w_array.compile(ctx)
            ctx.emit('STORE_MEMBER')

    def str(self):
        return u'MemberAssignmentOperation (%s, %s, %s)' % (
            self.left.str(),
            unicode(self.operand),
            self.right.str())


class Unconditional(Statement):
    def __init__(self, count):
        self.count = count


class Break(Unconditional):
    def compile(self, ctx):
        assert self.count is None
        ctx.emit('LOAD_NULL')
        ctx.emit_break()


class Continue(Unconditional):
    def compile(self, ctx):
        assert self.count is None
        ctx.emit('LOAD_NULL')
        ctx.emit_continue()


class If(Node):
    """ A very simple if
    """
    def __init__(self, condition, true_branch, else_branch=None):
        self.condition = condition
        self.true_branch = true_branch
        self.else_branch = else_branch

    def compile(self, ctx):
        self.condition.compile(ctx)
        endif = ctx.prealocate_label()
        endthen = ctx.prealocate_label()
        ctx.emit('JUMP_IF_FALSE', endthen)
        self.true_branch.compile(ctx)
        ctx.emit('JUMP', endif)
        ctx.emit_label(endthen)

        if self.else_branch is not None:
            self.else_branch.compile(ctx)
        else:
            ctx.emit('LOAD_NULL')

        ctx.emit_label(endif)

    def str(self):
        true_branch = self._indent_block(self.true_branch)
        if self.else_branch:
            else_branch = self._indent_block(self.else_branch)
            return u'If (%s,\n%s,\n%s\n)' % (self.condition.str(),
                                             true_branch,
                                             else_branch)
        else:
            return u'If (%s,\n%s\n)' % (self.condition.str(),
                                        true_branch)


class WhileBase(Statement):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class While(WhileBase):
    def compile(self, ctx):
        ctx.emit('LOAD_NULL')
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

    def str(self):
        body = self._indent_block(self.body)
        return u'While (%s,\n%s\n)' % (self.condition.str(), body)


class For(Statement):
    def __init__(self, setup, condition, update, body):
        self.setup = setup
        self.condition = condition
        self.update = update
        self.body = body

    def compile(self, ctx):
        self.setup.compile(ctx)
        ctx.emit('DISCARD_TOP')

        ctx.emit('LOAD_NULL')

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

    def str(self):
        body = self._indent_block(self.body)
        return u'For (%s, %s, %s,\n%s\n)' % (self.setup.str(),
                                             self.condition.str(),
                                             self.update.str(), body)


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
        ctx.emit('LOAD_NULL')
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

    def str(self):
        body = self._indent_block(self.body)
        return u'Foreach (%s, %s, %s,\n%s\n)' % (self.w_object.str(),
                                                 self.key.str(),
                                                 self.variable.str(), body)


class Print(Node):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit('PRINT')

    def str(self):
        return u'Print (%s)' % self.expr.str()


class Return(Statement):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        if self.expr is None:
            ctx.emit('LOAD_NULL')
        else:
            self.expr.compile(ctx)
        ctx.emit('RETURN')

    def str(self):
        if self.expr:
            return u'Return (%s)' % self.expr.str()
        else:
            return u'Return'


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
            ctx.emit('LOAD_NULL')

    def str(self):
        string = []
        for node in self.nodes:
            for line in node.str().split(u"\n"):
                string.append(line)
        body = self._indent(string)
        return u'Block (\n%s\n)' % body


def create_binary_op(name):
    class BinaryOp(Expression):
        def __init__(self, left, right):
            self.left = left
            self.right = right

        def compile(self, ctx):
            self.left.compile(ctx)
            self.right.compile(ctx)
            ctx.emit(name)

        def str(self):
            return unicode(name) + u' (%s, %s)' % (self.left.str(),
                                                   self.right.str())
    BinaryOp.__name__ = name
    return BinaryOp


def create_unary_op(name):
    class UnaryOp(Expression):
        def __init__(self, expr):
            self.expr = expr

        def compile(self, ctx):
            self.expr.compile(ctx)
            ctx.emit(name)

        def str(self):
            return unicode(name) + u' (%s)' % (self.expr.str(),)
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

    def str(self):
        return u'And (%s, %s)' % (self.left.str(), self.right.str())


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

    def str(self):
        return u'Or (%s, %s)' % (self.left.str(), self.right.str())

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
