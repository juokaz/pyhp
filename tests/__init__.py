import py
from pyhp.main import bytecode, ast, main
from pyhp.interpreter import Interpreter


class TestBase(object):
    def setup_method(self, meth):
        self.tmpname = meth.im_func.func_name

    def run(self, code):
        bc = bytecode('/tmp/example.php', code)
        intrepreter = Interpreter()
        return intrepreter.run_return(bc)

    def bytecode(self, code):
        return bytecode('/tmp/example.php', code)

    def ast(self, code):
        return ast(code)

    def main(self, argv):
        return main(argv)

    def store(self, code):
        tmpdir = py.path.local.make_numbered_dir('pyhp')
        phpfile = tmpdir.join(self.tmpname + '.php')
        f = open(str(phpfile), 'w')
        f.write(code.encode('utf8'))
        f.close()
        return str(phpfile)
