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
