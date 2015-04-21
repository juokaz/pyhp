from tests import TestBase

class TestMain(TestBase):
    def test_running(self, capfd):
        out = self.run("""$x = 1;
        print $x;""", capfd)
        assert out == "1"

    def test_running_comments(self, capfd):
        out = self.run("""// $x is a variable
        $x = 1;
        print $x;""", capfd)
        assert out == "1"

    def test_running_comments_block(self, capfd):
        out = self.run("""/*
         * $x is a variable
         */
        $x = 1;
        print $x;""", capfd)
        assert out == "1"

    def test_running_assigning_variable_twice(self, capfd):
        out = self.run("""$x = 1;
        $x= 5;
        print $x;""", capfd)
        assert out == "5"

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

    def test_array(self, capfd):
        out = self.run("""$x = [1, 2, 3];
        print $x;""", capfd)
        assert out == "[1: 2, 0: 1, 2: 3]"

    def test_array_old_syntax(self, capfd):
        out = self.run("""$x = array(1, 2, 3);
        print $x;""", capfd)
        assert out == "[1: 2, 0: 1, 2: 3]"

    def test_array_access(self, capfd):
        out = self.run("""$x = [1, 2, 3];
        print $x[1];""", capfd)
        assert out == "2"

    def test_array_write(self, capfd):
        out = self.run("""$x = [1, 2, 3];
        $x[1] = 5;
        print $x;""", capfd)
        assert out == "[1: 5, 0: 1, 2: 3]"

