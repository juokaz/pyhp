from tests import TestBase


class TestFunctions(TestBase):
    def test_function_call(self):
        out = self.run("""function hello($a) {
            print 'Hello world';
        }

        hello('Hello world');""")
        assert out == "Hello world"

    def test_function_defined_twice(self):
        try:
            self.run("""function strlen($a) {
                print 1;
            }

            strlen('Hello world');""")
        except Exception as e:
            assert str(e) == 'Function strlen alredy declared'
        else:
            assert False is True

    def test_function_call_multiple_args(self):
        out = self.run("""function hello($a, $b) {
            print $a;
            print ' ';
            print $b;
        }

        hello('Hello', 'world');""")
        assert out == "Hello world"

    def test_function_call_return(self):
        out = self.run("""function hello($a) {
            return $a;
        }

        print hello('Hello world');""")
        assert out == "Hello world"

    def test_function_call_empty_return(self):
        out = self.run("""function hello($a) {
            return;
        }

        print hello('Hello world');""")
        assert out == "null"

    def test_function_call_no_return(self):
        out = self.run("""function hello($a) {

        }

        print hello('Hello world');""")
        assert out == "null"

    def test_function_call_return_null(self):
        out = self.run("""function hello($a) {
            return null;
        }

        print hello('Hello world');""")
        assert out == "null"

    def test_function_call_return_breaks(self):
        out = self.run("""function hello() {
            print 'hello';
            return;
            print 'world';
        }

        hello();""")
        assert out == "hello"

    def test_function_two_returns(self):
        # the else branch generates a RETURN bytecode, which is immediately
        # followed by a auto-added RETURN bytecode for the function itself
        # stack size estimation shoud understand that the last RETURN is not
        # reachable
        out = self.run("""function hello() {
            if (1 > 2) {
                return 2;
            } else {
                return 3;
            }
        }

        print hello();""")
        assert out == "3"
