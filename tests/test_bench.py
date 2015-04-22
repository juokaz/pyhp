from tests import TestBase

class TestBench(TestBase):
    def test_simple(self, capfd):
        out = self.run("""function simple() {
          $a = 0;
          for ($i = 0; $i < 100; $i++)
            $a++;

          $thisisanotherlongname = 0;
          for ($thisisalongname = 0; $thisisalongname < 100; $thisisalongname++)
            $thisisanotherlongname++;
        }

        simple();""", capfd)
        assert out == ""

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

    def test_mandel(self, capfd):
        out = self.run("""function mandel() {
          $w1=5;
          $h1=10;
          $recen=-.45;
          $imcen=0.0;
          $r=0.7;
          $s=0;  $rec=0;  $imc=0;  $re=0;  $im=0;  $re2=0;  $im2=0;
          $x=0;  $y=0;  $w2=0;  $h2=0;  $color=0;
          $s=2*$r/$w1;
          $w2=40;
          $h2=12;
          for ($y=0 ; $y<=$w1; $y=$y+1) {
            $imc=$s*($y-$h2)+$imcen;
            for ($x=0 ; $x<=$h1; $x=$x+1) {
              $rec=$s*($x-$w2)+$recen;
              $re=$rec;
              $im=$imc;
              $color=1000;
              $re2=$re*$re;
              $im2=$im*$im;
              while( ((($re2+$im2)<1000000) && $color>0)) {
                $im=$re*$im*2+$imc;
                $re=$re2-$im2+$rec;
                $re2=$re*$re;
                $im2=$im*$im;
                $color=$color-1;
              }
              if ( $color==0 ) {
                print "_";
              } else {
                print "#";
              }
            }
            print "<br>";
          }
        }

        mandel();""", capfd)
        assert out == "###########<br>###########<br>###########<br>###########<br>###########<br>###########<br>"

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
        assert out == "10 100\n"

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
