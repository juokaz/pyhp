from tests import TestBase

class TestBinaryOperations(TestBase):
    def test_string_join(self, capfd):
        out = self.run("""$hello = 'Hello';
        $world = 'World';
        $x = $hello . ' ' . $world;
        print $x;""", capfd)
        assert out == "Hello World"

    def test_increase(self, capfd):
        out = self.run("""$i = 1;
        $i++;
        print $i;""", capfd)
        assert out == "2"

    def test_decrease(self, capfd):
        out = self.run("""$i = 1;
        $i--;
        print $i;""", capfd)
        assert out == "0"

    def test_increase_assign(self, capfd):
        out = self.run("""$i = 1;
        $i += 2;
        print $i;""", capfd)
        assert out == "3"

    def test_decrease_assign(self, capfd):
        out = self.run("""$i = 2;
        $i -= 2;
        print $i;""", capfd)
        assert out == "0"
