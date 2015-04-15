import py
from rpython.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function
from pyhp import pyhpdir
from pyhp import bytecode

grammar = py.path.local(pyhpdir).join('grammar.txt').read("rt")
regexs, rules, ToAST = parse_ebnf(grammar)
_parse = make_parse_function(regexs, rules, eof=True)

class Node(object):
    """ The abstract AST node
    """
    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self == other

class Block(Node):
    """ A list of statements
    """
    def __init__(self, stmts):
        self.stmts = stmts

    def compile(self, ctx):
        for stmt in self.stmts:
            stmt.compile(ctx)

class Stmt(Node):
    """ A single statement
    """
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(bytecode.DISCARD_TOP)

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
        # convert the integer to W_FloatObject already here
        from pyhp.interpreter import W_FloatObject
        w = W_FloatObject(self.floatval)
        ctx.emit(bytecode.LOAD_CONSTANT, ctx.register_constant(w))

class BinOp(Node):
    """ A binary operation
    """
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.left.compile(ctx)
        self.right.compile(ctx)
        ctx.emit(bytecode.BINOP[self.op])

class Variable(Node):
    """ Variable reference
    """
    def __init__(self, varname):
        self.varname = varname

    def compile(self, ctx):
        ctx.emit(bytecode.LOAD_VAR, ctx.register_var(self.varname))

class Assignment(Node):
    """ Assign to a variable
    """
    def __init__(self, varname, expr):
        self.varname = varname
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(bytecode.ASSIGN, ctx.register_var(self.varname))

class While(Node):
    """ Simple loop
    """
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def compile(self, ctx):
        pos = len(ctx.data)
        self.cond.compile(ctx)
        ctx.emit(bytecode.JUMP_IF_FALSE, 0)
        jmp_pos = len(ctx.data) - 1
        self.body.compile(ctx)
        ctx.emit(bytecode.JUMP_BACKWARD, pos)
        ctx.data[jmp_pos] = chr(len(ctx.data))

class If(Node):
    """ A very simple if
    """
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def compile(self, ctx):
        self.cond.compile(ctx)
        ctx.emit(bytecode.JUMP_IF_FALSE, 0)
        jmp_pos = len(ctx.data) - 1
        self.body.compile(ctx)
        ctx.data[jmp_pos] = chr(len(ctx.data))

class Print(Node):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(bytecode.PRINT, 0)

class Transformer(object):
    """ Transforms AST from the obscure format given to us by the ennfparser
    to something easier to work with
    """
    def _grab_stmts(self, star):
        stmts = []
        while len(star.children) == 2:
            stmts.append(self.visit_stmt(star.children[0]))
            star = star.children[1]
        stmts.append(self.visit_stmt(star.children[0]))
        return stmts

    def visit_main(self, node):
        stmts = self._grab_stmts(node.children[0])
        return Block(stmts)

    def visit_stmt(self, node):
        if len(node.children) == 2:
            return Stmt(self.visit_expr(node.children[0]))
        if len(node.children) == 4:
            return Assignment(node.children[0].additional_info,
                              self.visit_expr(node.children[2]))
        if node.children[0].additional_info == 'while':
            cond = self.visit_expr(node.children[2])
            stmts = self._grab_stmts(node.children[5])
            return While(cond, Block(stmts))
        if node.children[0].additional_info == 'if':
            cond = self.visit_expr(node.children[2])
            stmts = self._grab_stmts(node.children[5])
            return If(cond, Block(stmts))
        if node.children[0].additional_info == 'print':
            return Print(self.visit_expr(node.children[1]))
        raise NotImplementedError

    def visit_expr(self, node):
        if len(node.children) == 1:
            return self.visit_atom(node.children[0])
        return BinOp(node.children[1].additional_info,
                     self.visit_atom(node.children[0]),
                     self.visit_expr(node.children[2]))

    def visit_atom(self, node):
        chnode = node.children[0]
        if chnode.symbol == 'DECIMAL':
            return ConstantInt(int(chnode.additional_info))
        if chnode.symbol == 'VARIABLE':
            return Variable(chnode.additional_info)
        if chnode.symbol == 'FLOAT':
            return ConstantFloat(float(chnode.additional_info))
        raise NotImplementedError

transformer = Transformer()

def parse(source):
    """ Parse the source code and produce an AST
    """
    return transformer.visit_main(_parse(source))
