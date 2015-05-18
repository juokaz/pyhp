import py
from pyhp.main import run, run_return, bytecode, ast


class TestBase(object):
    def setup_method(self, meth):
        self.tmpname = meth.im_func.func_name

    def run(self, code, capfd, expected_exitcode=0,
            cgi=False, args=[]):
        filename = self._init(code)
        r = run(filename)
        out, err = capfd.readouterr()
        assert r == expected_exitcode
        return out

    def run_return(self, code):
        filename = self._init(code)
        return run_return(filename)

    def bytecode(self, code):
        filename = self._init(code)
        return bytecode(filename)

    def ast(self, code):
        filename = self._init(code)
        return ast(filename)

    def _init(self, code):
        tmpdir = py.path.local.make_numbered_dir('pyhp')
        phpfile = tmpdir.join(self.tmpname + '.php')
        f = open(str(phpfile), 'w')
        f.write(code.encode('utf8'))
        f.close()
        return str(phpfile)
