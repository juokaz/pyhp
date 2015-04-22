from tests import TestBase

class TestFunctions(TestBase):
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
