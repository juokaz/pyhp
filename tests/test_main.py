import py, re, tempfile, os, sys
from pyhp.main import main

class TestMain(object):
    def setup_method(self, meth):
        self.tmpname = meth.im_func.func_name

    def run(self, code, capfd, expected_exitcode=0,
            cgi=False, args=[]):
        tmpdir = py.path.local.make_numbered_dir('pyhp')
        phpfile = tmpdir.join(self.tmpname + '.php')
        phpfile.write(code)
        r = main([None, str(phpfile)])
        out, err = capfd.readouterr()
        assert r == expected_exitcode
        assert not err
        return out

    def test_running(self, capfd):
        out = self.run("""$x = 1;
        print $x;""", capfd)
        assert out == "1"

    def test_running_opening_tag(self, capfd):
        out = self.run("""<?php
        $x = 1;
        print $x;""", capfd)
        assert out == "1"

    def test_strinval(self, capfd):
        out = self.run("""$x = 'Hello world';
        print $x;""", capfd)
        assert out == "Hello world"
