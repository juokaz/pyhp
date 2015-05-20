# -*- coding: utf-8 -*-

from tests import TestBase


class TestDatatypes(TestBase):
    def test_string_single_quotes(self):
        out = self.run("""$x = 'Hello world';
        print $x;""")
        assert out == "Hello world"

    def test_string_unicode(self):
        out = self.run(u"""$x = 'Juozas Kaziukėnas';
        print $x[13];""".encode('utf-8'))
        assert out == u"ė"

    def test_string_array_access(self):
        out = self.run("""$x = 'Hello world';
        print $x[1];""")
        assert out == "e"

    def test_string_single_quotes_embed(self):
        out = self.run("""$y = 'world';
        $z = 1;
        $x = 'Hello $y $z';
        print $x;""")
        assert out == "Hello $y $z"

    def test_string_double_quotes(self):
        out = self.run("""$x = "Hello world\n";
        print $x;""")
        assert out == "Hello world\n"

    def test_string_double_quotes_embed(self):
        out = self.run("""$y = 'world';
        $z = 1;
        $x = "Hello $y $z";
        print $x;""")
        assert out == "Hello world 1"

    def test_string_curly_embed(self):
        out = self.run("""$y = 'world';
        $x = "Hello {$y}";
        print $x;""")
        assert out == "Hello world"

    def test_string_embed_array(self):
        out = self.run("""$y = ['world'];
        $x = "Hello {$y[0]}";
        print $x;""")
        assert out == "Hello world"

    def test_string_embed_array_variable_index(self):
        out = self.run("""$y = ['world'];
        $i = 0;
        $x = "Hello {$y[$i]}";
        print $x;""")
        assert out == "Hello world"

    def test_boolean(self):
        out = self.run("""$x = true;
        print $x;""")
        assert out == "true"

    def test_float(self):
        out = self.run("""$x = -1.3;
        print $x;""")
        assert out == "-1.3"

    def test_float_short(self):
        out = self.run("""$x = .3;
        print $x;""")
        assert out == "0.3"

    def test_array(self):
        out = self.run("""$x = [1, 2, 3];
        print_r($x);""")
        assert out == "Array\n(\n\t[0] => 1\n\t[1] => 2\n\t[2] => 3\n)\n"

    def test_print_array(self):
        out = self.run("""$x = [1, 2, 3];
        print $x;""")
        assert out == "Array"

    def test_empty_array(self):
        out = self.run("""$x = [];
        print_r($x);""")
        assert out == "Array\n(\n)\n"

    def test_nested_array(self):
        out = self.run("""$x = [1, 2, [3, 4, 5]];
        print_r($x);""")
        assert out == "Array\n(\n\t[0] => 1\n\t[1] => 2\n\t[2] => Array" + \
            "\n\t(\n\t\t[0] => 3\n\t\t[1] => 4\n\t\t[2] => 5\n\t)\n)\n"

    def test_array_old_syntax(self):
        out = self.run("""$x = array(1, 2, 3);
        print_r($x);""")
        assert out == "Array\n(\n\t[0] => 1\n\t[1] => 2\n\t[2] => 3\n)\n"

    def test_array_access(self):
        out = self.run("""$x = [1, 2, 3];
        print $x[1];""")
        assert out == "2"

    def test_array_from_list_to_dict(self):
        out = self.run("""$x = [1, 2, 3];
        $x['x'] = 4;
        print $x['x'];""")
        assert out == "4"

    def test_nested_array_access(self):
        out = self.run("""$x = [1, 2, [3, 4, 5]];
        print $x[2][1];""")
        assert out == "4"

    def test_array_write(self):
        out = self.run("""$x = [1, 2, 3];
        $x[1] = 5;
        print_r($x);""")
        assert out == "Array\n(\n\t[0] => 1\n\t[1] => 5\n\t[2] => 3\n)\n"
