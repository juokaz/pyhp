from tests import TestBase


class TestFibonacci(TestBase):
    def test_running(self, capfd):
        out = self.run("""function fib ($n)
        {
           return(($n < 2) ? 1 : fib($n - 2) + fib($n - 1));
        }

        print fib(9);""", capfd)
        assert out == "55"
