from tests import TestBase


class TestScopes(TestBase):
    def test_function_call_pass_by_value(self):
        out = self.run("""function test($a) {
            $a = 3;
        }

        $i = 5;
        test($i);

        print $i;
        """)
        assert out == "5"

    def test_function_call_pass_by_reference(self):
        out = self.run("""function test(&$a) {
            $a = 3;
        }

        $i = 5;
        test($i);

        print $i;
        """)
        assert out == "3"

    def test_function_call_array_pass_by_value(self):
        out = self.run("""function test($a) {
            $a[0] = 3;
        }

        $i = [5];
        test($i);

        print $i[0];
        """)
        assert out == "5"

    def test_function_call_array_pass_by_reference(self):
        out = self.run("""function test(&$a) {
            $a[0] = 3;
        }

        $i = [5];
        test($i);

        print $i[0];
        """)
        assert out == "3"

    def test_function_call_local_vars(self):
        out = self.run("""function test() {
            $i = 5;
            return $i + 1;
        }

        $i = 1;
        $i = test();

        print $i;
        """)
        assert out == "6"

    def test_function_out_of_scope(self):
        try:
            self.run("""function test() {
                return $a;
            }

            $a = 1;
            $i = test();

            print $i;
            """)
        except Exception as e:
            assert str(e) == 'Variable $a is not set'
        else:
            assert False is True

    def test_function_global(self):
        out = self.run("""function test() {
            global $a, $c;
            return $a + $c + 1;
        }

        $a = 1;
        $b = 2;
        $c = 3;
        $i = test();

        print $i;
        """)
        assert out == "5"

    def test_function_write_to_global(self):
        out = self.run("""function test() {
            global $a;
            $a = 3;
        }

        $a = 1;
        test();

        print $a;
        """)
        assert out == "3"

    def test_function_recursive_scope(self):
        out = self.run("""function test($a) {
            if ($a < 100) {
                return test($a + 1);
            }
            return $a;
        }

        $a = 1;
        $i = test($a);

        print $i;
        """)
        assert out == "100"

    def test_define_constant(self):
        out = self.run("""define("TEST", 1);

        print TEST;
        """)
        assert out == "1"

    def test_define_constant_twice(self):
        out = self.run("""define("TEST", 1);
        print define("TEST", 1);
        """)
        assert out == "false"

    def test_constant_defined_in_a_function(self):
        out = self.run("""function test() {
            define("TEST", 1);
            return TEST;
        }

        print test();
        """)
        assert out == "1"

    def test_constant_accessed_from_a_different_function(self):
        out = self.run("""function test() {
            define("TEST", 1);
        }

        function test2() {
            return TEST;
        }

        test();

        print test2();
        """)
        assert out == "1"
