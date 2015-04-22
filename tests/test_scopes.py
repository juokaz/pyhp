from tests import TestBase

class TestScopes(TestBase):
    def test_function_out_of_scope(self, capfd):
        try:
            out = self.run("""function test() {
                return $a;
            }

            $a = 1;
            $i = test();

            print $i;
            """, capfd)
        except Exception as e:
            assert str(e) == 'Variable 1 ($a) is not set'
        else:
            assert False == True

    def test_function_global(self, capfd):
        out = self.run("""function test() {
            global $a, $c;
            return $a + $c + 1;
        }

        $a = 1;
        $b = 2;
        $c = 3;
        $i = test();

        print $i;
        """, capfd)
        assert out == "5"

    def test_function_write_to_global(self, capfd):
        out = self.run("""function test() {
            global $a;
            $a = 3;
        }

        $a = 1;
        test();

        print $a;
        """, capfd)
        assert out == "3"

    def test_function_recursive_scope(self, capfd):
        out = self.run("""function test($a) {
            if ($a < 100) {
                return test($a + 1);
            }
            return $a;
        }

        $a = 1;
        $i = test($a);

        print $i;
        """, capfd)
        assert out == "100"
