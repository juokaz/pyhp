from tests import TestBase

class TestDatatypes(TestBase):
    def test_string_single_quotes(self, capfd):
        out = self.run("""$x = 'Hello world';
        print $x;""", capfd)
        assert out == "Hello world"

    def test_string_array_access(self, capfd):
        out = self.run("""$x = 'Hello world';
        print $x[1];""", capfd)
        assert out == "e"

    def test_string_single_quotes_embed(self, capfd):
        out = self.run("""$y = 'world';
        $z = 1;
        $x = 'Hello $y $z';
        print $x;""", capfd)
        assert out == "Hello $y $z"

    def test_string_double_quotes(self, capfd):
        out = self.run("""$x = "Hello world\n";
        print $x;""", capfd)
        assert out == "Hello world\n"

    def test_string_double_quotes_embed(self, capfd):
        out = self.run("""$y = 'world';
        $z = 1;
        $x = "Hello $y $z";
        print $x;""", capfd)
        assert out == "Hello world 1"

    def test_string_curly_embed(self, capfd):
        out = self.run("""$y = 'world';
        $x = "Hello {$y}";
        print $x;""", capfd)
        assert out == "Hello world"

    def test_string_embed_array(self, capfd):
        out = self.run("""$y = ['world'];
        $x = "Hello {$y[0]}";
        print $x;""", capfd)
        assert out == "Hello world"

    def test_string_embed_array_variable_index(self, capfd):
        out = self.run("""$y = ['world'];
        $i = 0;
        $x = "Hello {$y[$i]}";
        print $x;""", capfd)
        assert out == "Hello world"

    def test_boolean(self, capfd):
        out = self.run("""$x = true;
        print $x;""", capfd)
        assert out == "true"

    def test_float(self, capfd):
        out = self.run("""$x = -1.3;
        print $x;""", capfd)
        assert out == "-1.3"

    def test_float_short(self, capfd):
        out = self.run("""$x = .3;
        print $x;""", capfd)
        assert out == "0.3"

    def test_array(self, capfd):
        out = self.run("""$x = [1, 2, 3];
        print $x;""", capfd)
        assert out == "[1: 2, 0: 1, 2: 3]"

    def test_empty_array(self, capfd):
        out = self.run("""$x = [];
        print $x;""", capfd)
        assert out == "[]"

    def test_nested_array(self, capfd):
        out = self.run("""$x = [1, 2, [3, 4, 5]];
        print $x;""", capfd)
        assert out == "[1: 2, 0: 1, 2: [1: 4, 0: 3, 2: 5]]"

    def test_array_old_syntax(self, capfd):
        out = self.run("""$x = array(1, 2, 3);
        print $x;""", capfd)
        assert out == "[1: 2, 0: 1, 2: 3]"

    def test_array_access(self, capfd):
        out = self.run("""$x = [1, 2, 3];
        print $x[1];""", capfd)
        assert out == "2"

    def test_nested_array_access(self, capfd):
        out = self.run("""$x = [1, 2, [3, 4, 5]];
        print $x[2][1];""", capfd)
        assert out == "4"

    def test_array_write(self, capfd):
        out = self.run("""$x = [1, 2, 3];
        $x[1] = 5;
        print $x;""", capfd)
        assert out == "[1: 5, 0: 1, 2: 3]"
