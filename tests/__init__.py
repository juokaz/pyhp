import py
from pyhp.main import run, run_return, bytecode, ast


class TestBase(object):
    def setup_method(self, meth):
        self.tmpname = meth.im_func.func_name

    def run(self, code, capfd, expected_exitcode=0,
            cgi=False, args=[]):
        r = run('/tmp/example.php', code)
        out, err = capfd.readouterr()
        assert r == expected_exitcode
        return out

    def run_return(self, code):
        return run_return('/tmp/example.php', code)

    def bytecode(self, code):
        return bytecode('/tmp/example.php', code)

    def ast(self, code):
        return ast(code)

    def store(self, code):
        tmpdir = py.path.local.make_numbered_dir('pyhp')
        phpfile = tmpdir.join(self.tmpname + '.php')
        f = open(str(phpfile), 'w')
        f.write(code.encode('utf8'))
        f.close()
        return str(phpfile)
