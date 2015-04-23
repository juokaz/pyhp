from tests import TestBase

class TestStdlib(TestBase):
    def test_string_length(self, capfd):
        out = self.run("""$x = 'Hello world';
        print strlen($x);""", capfd)
        assert out == "11"
