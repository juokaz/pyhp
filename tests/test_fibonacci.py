from tests import TestBase

class TestFibonacci(TestBase):
    def test_running(self, capfd):
        out = self.run("""function fib ($n)
        {
           if ($n == 0) {
              return 0;
           }

           if ($n == 1)
           {
              return 1;
           }

           return fib( $n - 1 ) + fib( $n - 2 );
        }

        print fib(10);""", capfd)
        assert out == "55"
