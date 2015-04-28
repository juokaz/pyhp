from tests import TestBase

class TestAsignmentOperations(TestBase):
    def test_assign_print(self, capfd):
        out = self.run("""$i = 1;
        print $i = 2;""", capfd)
        assert out == "2"

    def test_increase(self, capfd):
        out = self.run("""$i = 1;
        $i++;
        print $i;""", capfd)
        assert out == "2"

    def test_array_increase(self, capfd):
        out = self.run("""$i = [1];
        $i[0]++;
        print $i[0];""", capfd)
        assert out == "2"

    def test_decrease(self, capfd):
        out = self.run("""$i = 1;
        $i--;
        print $i;""", capfd)
        assert out == "0"

    def test_decrease_assign(self, capfd):
        out = self.run("""$i = 1;
        $i = $i--;
        print $i;""", capfd)
        assert out == "1"

    def test_pre_decrease(self, capfd):
        out = self.run("""$i = 1;
        print --$i;""", capfd)
        assert out == "0"

    def test_post_decrease(self, capfd):
        out = self.run("""$i = 1;
        print $i--;""", capfd)
        assert out == "1"

    def test_increase_assign(self, capfd):
        out = self.run("""$i = 1;
        $i += 2;
        print $i;""", capfd)
        assert out == "3"

    def test_sub_assign(self, capfd):
        out = self.run("""$i = 2;
        $i -= 2;
        print $i;""", capfd)
        assert out == "0"

    def test_string_join(self, capfd):
        out = self.run("""$hello = 'Hello';
        $world = 'World';
        $x = $hello . ' ' . $world;
        print $x;""", capfd)
        assert out == "Hello World"
