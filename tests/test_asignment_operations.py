from tests import TestBase


class TestAsignmentOperations(TestBase):
    def test_assign_print(self):
        out = self.run("""$i = 1;
        print $i = 2;""")
        assert out == "2"

    def test_increase(self):
        out = self.run("""$i = 1;
        $i++;
        print $i;""")
        assert out == "2"

    def test_array_increase(self):
        out = self.run("""$i = [1];
        $i[0]++;
        print $i[0];""")
        assert out == "2"

    def test_decrease(self):
        out = self.run("""$i = 1;
        $i--;
        print $i;""")
        assert out == "0"

    def test_decrease_assign(self):
        out = self.run("""$i = 1;
        $i = $i--;
        print $i;""")
        assert out == "1"

    def test_pre_decrease(self):
        out = self.run("""$i = 1;
        print --$i;""")
        assert out == "0"

    def test_post_decrease(self):
        out = self.run("""$i = 1;
        print $i--;""")
        assert out == "1"

    def test_increase_assign(self):
        out = self.run("""$i = 1;
        $i += 2;
        print $i;""")
        assert out == "3"

    def test_sub_assign(self):
        out = self.run("""$i = 2;
        $i -= 2;
        print $i;""")
        assert out == "0"

    def test_string_join(self):
        out = self.run("""$hello = 'Hello';
        $world = 'World';
        $x = $hello . ' ' . $world;
        print $x;""")
        assert out == "Hello World"

    def test_string_join_does_not_modify_original(self):
        out = self.run("""$hello = 'Hello';
        $x = $hello . ' World';
        print $hello;
        print $x;""")
        assert out == "HelloHello World"
