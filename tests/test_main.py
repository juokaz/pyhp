from tests import TestBase

class TestMain(TestBase):
    def test_running(self, capfd):
        out = self.run("""$x = 1;
        print $x;""", capfd)
        assert out == "1"

    def test_running_opening_tag(self, capfd):
        out = self.run("""<?php
        $x = 1;
        print $x;""", capfd)
        assert out == "1"

    def test_string(self, capfd):
        out = self.run("""$x = 'Hello world';
        print $x;""", capfd)
        assert out == "Hello world"

    def test_string_double_quotes(self, capfd):
        out = self.run("""$x = "Hello world";
        print $x;""", capfd)
        assert out == "Hello world"

    def test_boolean(self, capfd):
        out = self.run("""$x = true;
        print $x;""", capfd)
        assert out == "true"

