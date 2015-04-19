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

    def test_function_call(self, capfd):
        out = self.run("""function hello($a) {
            print 'Hello world';
        }

        hello('Hello world');""", capfd)
        assert out == "Hello world"

    def test_function_call_multiple_args(self, capfd):
        out = self.run("""function hello($a, $b) {
            print $a;
            print ' ';
            print $b;
        }

        hello('Hello', 'world');""", capfd)
        # todo arguments get inverted
        assert out == "Hello world"

    def test_function_call_return(self, capfd):
        out = self.run("""function hello($a) {
            return $a;
        }

        print hello('Hello world');""", capfd)
        assert out == "Hello world"

    def test_function_call_empty_return(self, capfd):
        out = self.run("""function hello($a) {
            return;
        }

        print hello('Hello world');""", capfd)
        assert out == "null"

    def test_function_call_no_return(self, capfd):
        out = self.run("""function hello($a) {

        }

        print hello('Hello world');""", capfd)
        assert out == "null"

    def test_function_call_return_null(self, capfd):
        out = self.run("""function hello($a) {
            return null;
        }

        print hello('Hello world');""", capfd)
        assert out == "null"

    def test_function_call_return_breaks(self, capfd):
        out = self.run("""function hello() {
            print 'hello';
            return;
            print 'world';
        }

        hello();""", capfd)
        assert out == "hello"

    def test_function_call_local_vars(self, capfd):
        out = self.run("""function test($x) {
            return $x + 1;
        }

        $i = 1;
        $i = test($i);

        print $i;
        """, capfd)
        assert out == "2"

    def test_string(self, capfd):
        out = self.run("""$x = 'Hello world';
        print $x;""", capfd)
        assert out == "Hello world"

    def test_string_double_quotes(self, capfd):
        out = self.run("""$x = "Hello world";
        print $x;""", capfd)
        assert out == "Hello world"
