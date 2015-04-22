from tests import TestBase

class TestBench(TestBase):
    def test_simpleucall(self, capfd):
        out = self.run("""function hallo($a) {
        }

        function simpleucall() {
          for ($i = 0; $i < 10; $i++)
            hallo("hallo");
        }

        simpleucall();""", capfd)
        assert out == ""

    def test_simpleudcall(self, capfd):
        out = self.run("""function simpleudcall() {
          for ($i = 0; $i < 10; $i++)
            hallo2("hallo");
        }

        function hallo2($a) {
        }

        simpleudcall();""", capfd)
        assert out == ""


    def test_ackermann(self, capfd):
        out = self.run("""function Ack($m, $n) {
          if($m == 0) return $n+1;
          if($n == 0) return Ack($m-1, 1);
          return Ack($m - 1, Ack($m, ($n - 1)));
        }

        function ackermann($n) {
          $r = Ack(3,$n);
          print "Ack(3,$n): $r\n";
        }

        ackermann(1);""", capfd)
        assert out == "Ack(3,1): 13\n"
