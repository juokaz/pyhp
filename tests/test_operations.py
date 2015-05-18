from tests import TestBase


class TestMain(TestBase):
    def test_if(self):
        out = self.run("""
        $x = 1;
        if ($x >= 1) {
            print $x;
        }""")
        assert out == "1"

    def test_if_not(self):
        out = self.run("""
        $x = false;
        if (!$x) {
            print $x;
        }""")
        assert out == "false"

    def test_if_and(self):
        out = self.run("""
        $x = 1;
        $y = 2;
        if ($x >= 1 && $y < 2) {
            print $x;
        } else {
            print $y;
        }""")
        assert out == "2"

    def test_if_ignores_right_and(self):
        out = self.run("""function test() {
            print 'a';
            return 1;
        }
        $x = 1;
        if ($x < 1 && test() < 2) {
            print $x;
        } else {
            print 'OK';
        }""")
        assert out == "OK"

    def test_if_ignores_right_or(self):
        out = self.run("""function test() {
            print 'a';
            return 1;
        }
        $x = 1;
        if ($x < 2 || test() < 2) {
            print 'OK';
        }""")
        assert out == "OK"

    def test_if_equal(self):
        out = self.run("""
        $x = 1;
        if ($x == 1) {
            print $x;
        }""")
        assert out == "1"

    def test_inline_if(self):
        out = self.run("""
        $x = 1;
        print $x < 2 ? 1 : 0;""")
        assert out == "1"

    def test_while(self):
        out = self.run("""
        $x = 1;
        while ($x >= 1) {
            print $x;
            $x = $x - 1;
        }""")
        assert out == "1"

    def test_while_assignment(self):
        out = self.run("""
        $x = 2;
        while ($x--) {
            print $x;
        }""")
        assert out == "10"

    def test_while_lt(self):
        out = self.run("""
        $x = 1;
        while ($x < 10) {
            print $x;
            $x = $x + 1;
        }""")
        assert out == "123456789"

    def test_for(self):
        out = self.run("""
        for ($x = 1; $x < 10; $x++) {
            print $x;
        }""")
        assert out == "123456789"

    def test_for_comma(self):
        out = self.run("""
        for ($x = 1; printf("\n"), $x < 3; $x++) {
            print $x;
        }""")
        assert out == "\n1\n2\n"

    def test_for_break(self):
        out = self.run("""
        for ($x = 1; $x < 10; $x++) {
            if ($x > 3) {
                break;
            }
            print $x;
        }""")
        assert out == "123"

    def test_for_continue(self):
        out = self.run("""
        for ($x = 1; $x < 10; $x++) {
            if ($x < 3) {
                continue;
            }
            print $x;
        }""")
        assert out == "3456789"

    def test_foreach(self):
        out = self.run("""$x = [1, 2, 3];
        foreach ($x as $i) {
            print $i;
        }""")
        assert out == "123"

    def test_foreach_key(self):
        out = self.run("""$x = [3, 4, 5];
        foreach ($x as $i => $v) {
            print $i;
            print '-';
            print $v;
            print ' ';
        }""")
        assert out == "0-3 1-4 2-5 "

    def test_div(self):
        out = self.run("""$x = 6 / 2;
        print $x;""")
        assert out == "3"

    def test_float_div(self):
        out = self.run("""$x = 2 / 10;
        print $x;""")
        assert out == "0.2"

    def test_mod(self):
        out = self.run("""$x = 6 % 2;
        print $x;""")
        assert out == "0"

    def test_bitwise_rsh(self):
        out = self.run("""$x = 10 >> 1;
        print $x;""")
        assert out == "5"
