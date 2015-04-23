from tests import TestBase

class TestMain(TestBase):
    def test_if(self, capfd):
        out = self.run("""
        $x = 1;
        if ($x >= 1) {
            print $x;
        }""", capfd)
        assert out == "1"

    def test_if_and(self, capfd):
        out = self.run("""
        $x = 1;
        $y = 2;
        if ($x >= 1 && $y < 2) {
            print $x;
        } else {
            print $y;
        }""", capfd)
        assert out == "2"

    def test_if_equal(self, capfd):
        out = self.run("""
        $x = 1;
        if ($x == 1) {
            print $x;
        }""", capfd)
        assert out == "1"

    def test_inline_if(self, capfd):
        out = self.run("""
        $x = 1;
        print $x < 2 ? 1 : 0;""", capfd)
        assert out == "1"

    def test_while(self, capfd):
        out = self.run("""
        $x = 1;
        while ($x >= 1) {
            print $x;
            $x = $x - 1;
        }""", capfd)
        assert out == "1"

    def test_while_assignment(self, capfd):
        out = self.run("""
        $x = 2;
        while ($x--) {
            print $x;
        }""", capfd)
        assert out == "10"

    def test_while_lt(self, capfd):
        out = self.run("""
        $x = 1;
        while ($x < 10) {
            print $x;
            $x = $x + 1;
        }""", capfd)
        assert out == "123456789"

    def test_for(self, capfd):
        out = self.run("""
        for ($x = 1; $x < 10; $x++) {
            print $x;
        }""", capfd)
        assert out == "123456789"

    def test_div(self, capfd):
        out = self.run("""$x = 6 / 2;
        print $x;""", capfd)
        assert out == "3"

    def test_float_div(self, capfd):
        out = self.run("""$x = 2 / 10;
        print $x;""", capfd)
        assert out == "0.2"
