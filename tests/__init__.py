import py, re, tempfile, os, sys
from pyhp.main import run, bytecode

class TestBase(object):
    def setup_method(self, meth):
        self.tmpname = meth.im_func.func_name

    def run(self, code, capfd, expected_exitcode=0,
            cgi=False, args=[]):
        filename = self._init(code)
        r = run(filename)
        out, err = capfd.readouterr()
        assert r == expected_exitcode
        assert not err
        return out

    def bytecode(self, code):
        filename = self._init(code)
        return bytecode(filename)

    def _init(self, code):
        tmpdir = py.path.local.make_numbered_dir('pyhp')
        phpfile = tmpdir.join(self.tmpname + '.php')
        phpfile.write(code)
        return str(phpfile)
