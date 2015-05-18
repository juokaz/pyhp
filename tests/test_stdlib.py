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
        out = self.run("""$x = range(1, 3);
        print_r($x);""", capfd)
        assert out == "Array\n(\n\t[0] => 1\n\t[1] => 2\n\t[2] => 3\n)\n"

    def test_number_format(self, capfd):
        out = self.run("""$x = 3.456;
        print number_format($x, 2);""", capfd)
        assert out == "3.46"

    def test_number_format_less_than_zero(self, capfd):
        out = self.run("""$x = 0.045664;
        print number_format($x, 3);""", capfd)
        assert out == "0.046"

    def test_printf(self, capfd):
        out = self.run("""$x = 0.045664;
        printf("%.10f", $x);""", capfd)
        assert out == "0.0456640000"

    def test_printf_long(self, capfd):
        out = self.run("""$x = 0.045664;
        $y = 'string';
        printf("Number is %.3f this %s", $x, $y);""", capfd)
        assert out == "Number is 0.046 this string"

    def test_gettimeofday(self, capfd):
        out = self.run("""$time = gettimeofday();
        print $time['sec'];""", capfd)
        assert long(out) > 1430943462

    def test_ob_start(self, capfd):
        out = self.run("""ob_start();
        print 1;
        ob_end_clean();""", capfd)
        assert out == ""

    def test_ob_start_without_close(self, capfd):
        out = self.run("""ob_start();
        print 1;""", capfd)
        assert out == "1"

    def test_ob_start_nested(self, capfd):
        out = self.run("""ob_start();
        print 1;
        ob_start();
        print 2;
        ob_end_clean();
        ob_flush();""", capfd)
        assert out == "1"
