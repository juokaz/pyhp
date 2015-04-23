from tests import TestBase

class TestStdlib(TestBase):
    def test_strlen(self, capfd):
        out = self.run("""$x = 'Hello world';
        print strlen($x);""", capfd)
        assert out == "11"

    def test_str_repeat(self, capfd):
        out = self.run("""$x = 'Hello';
        print str_repeat($x, 2);""", capfd)
        assert out == "HelloHello"

    def test_string_length(self, capfd):
        out = self.run("""$x = 'Hello world';
        print strlen($x);""", capfd)
        assert out == "11"

    def test_range(self, capfd):
        out = self.run("""$x = range(1, 4);
        print $x;""", capfd)
        assert out == "[1: 1, 3: 3, 2: 2, 4: 4]"
