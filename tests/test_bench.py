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

    def test_ary3(self, capfd):
        out = self.run("""function ary3($n) {
          $X = [];
          $Y = [];
          for ($i=0; $i<$n; $i++) {
            $X[$i] = $i + 1;
            $Y[$i] = 0;
          }
          for ($k=0; $k<10; $k++) {
            for ($i=$n-1; $i>=0; $i--) {
              $Y[$i] += $X[$i];
            }
          }
          $last = $n-1;
          print "$Y[0] $Y[$last]\n";
        }

        ary3(10);""", capfd)
        assert out == "512 5120\n"

    def test_nestedloop(self, capfd):
        out = self.run("""function nestedloop($n) {
          $x = 0;
          for ($a=0; $a<$n; $a++)
            for ($b=0; $b<$n; $b++)
              for ($c=0; $c<$n; $c++)
                for ($d=0; $d<$n; $d++)
                  for ($e=0; $e<$n; $e++)
                    for ($f=0; $f<$n; $f++)
                     $x++;
          print "$x\n";
        }

        nestedloop(2);""", capfd)
        assert out == "64\n"
