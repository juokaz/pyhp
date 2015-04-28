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

    def test_simplecall(self, capfd):
        out = self.run("""function simplecall() {
          for ($i = 0; $i < 100; $i++)
            strlen("hallo");
        }

        simplecall();""", capfd)
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

    def test_ary(self, capfd):
        out = self.run("""function ary($n) {
          $X = [];
          $Y = [];
          for ($i=0; $i<$n; $i++) {
            $X[$i] = $i;
          }
          for ($i=$n-1; $i>=0; $i--) {
            $Y[$i] = $X[$i];
          }
          $last = $n-1;
          print "$Y[$last]\n";
        }

        ary(10);""", capfd)
        assert out == "9\n"

    def test_ary2(self, capfd):
        out = self.run("""function ary2($n) {
          $X = [];
          $Y = [];
          for ($i=0; $i<$n;) {
            $X[$i] = $i; ++$i;
            $X[$i] = $i; ++$i;
            $X[$i] = $i; ++$i;
            $X[$i] = $i; ++$i;
            $X[$i] = $i; ++$i;

            $X[$i] = $i; ++$i;
            $X[$i] = $i; ++$i;
            $X[$i] = $i; ++$i;
            $X[$i] = $i; ++$i;
            $X[$i] = $i; ++$i;
          }
          for ($i=$n-1; $i>=0;) {
            $Y[$i] = $X[$i]; --$i;
            $Y[$i] = $X[$i]; --$i;
            $Y[$i] = $X[$i]; --$i;
            $Y[$i] = $X[$i]; --$i;
            $Y[$i] = $X[$i]; --$i;

            $Y[$i] = $X[$i]; --$i;
            $Y[$i] = $X[$i]; --$i;
            $Y[$i] = $X[$i]; --$i;
            $Y[$i] = $X[$i]; --$i;
            $Y[$i] = $X[$i]; --$i;
          }
          $last = $n-1;
          print "$Y[$last]\n";
        }

        ary2(10);""", capfd)
        assert out == "9\n"

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

    def test_fibo(self, capfd):
        out = self.run("""function fibo_r($n){
            return(($n < 2) ? 1 : fibo_r($n - 2) + fibo_r($n - 1));
        }

        function fibo($n) {
          $r = fibo_r($n);
          print "$r\n";
        }

        fibo(10);""", capfd)
        assert out == "89\n"

    def test_hash1(self, capfd):
        out = self.run("""function hash1($n) {
          $X = [];
          for ($i = 1; $i <= $n; $i++) {
            $X[dechex($i)] = $i;
          }
          $c = 0;
          for ($i = $n; $i > 0; $i--) {
            if ($X[dechex($i)]) { $c++; }
          }
          print "$c\n";
        }

        hash1(10);""", capfd)
        assert out == "10\n"

    def test_heapsort(self, capfd):
        out = self.run("""function gen_random ($n) {
            global $LAST;
            return( ($n * ($LAST = ($LAST * IA + IC) % IM)) / IM );
        }

        function heapsort_r($n, &$ra) {
            $l = ($n >> 1) + 1;
            $ir = $n;

            while (1) {
          if ($l > 1) {
              $rra = $ra[--$l];
          } else {
              $rra = $ra[$ir];
              $ra[$ir] = $ra[1];
              if (--$ir == 1) {
            $ra[1] = $rra;
            return;
              }
          }
          $i = $l;
          $j = $l << 1;
          while ($j <= $ir) {
              if (($j < $ir) && ($ra[$j] < $ra[$j+1])) {
            $j++;
              }
              if ($rra < $ra[$j]) {
            $ra[$i] = $ra[$j];
            $j += ($i = $j);
              } else {
            $j = $ir + 1;
              }
          }
          $ra[$i] = $rra;
            }
        }

        function heapsort($N) {
          global $LAST;

          define("IM", 139968);
          define("IA", 3877);
          define("IC", 29573);

          $LAST = 42;
          $ary = [];
          for ($i=1; $i<=$N; $i++) {
            $ary[$i] = gen_random(1);
          }
          heapsort_r($N, $ary);
          printf("%.10f\n", $ary[$N]);
        }

        $LAST = 0;
        heapsort(3);""", capfd)
        assert out == "0.7290237769\n"

    def test_mkmatrix(self, capfd):
        out = self.run("""function mkmatrix ($rows, $cols) {
            $count = 1;
            $mx = array();
            for ($i=0; $i<$rows; $i++) {
              $mx[$i] = array();
          for ($j=0; $j<$cols; $j++) {
              $mx[$i][$j] = $count++;
          }
            }
            return($mx);
        }

        function mmult ($rows, $cols, $m1, $m2) {
            $m3 = array();
            for ($i=0; $i<$rows; $i++) {
              $m3[$i] = array();
              for ($j=0; $j<$cols; $j++) {
                $x = 0;
                  for ($k=0; $k<$cols; $k++) {
                    $x += $m1[$i][$k] * $m2[$k][$j];
                  }
                $m3[$i][$j] = $x;
              }
            }
            return($m3);
        }

        function matrix($n) {
          $SIZE = 10;
          $m1 = mkmatrix($SIZE, $SIZE);
          $m2 = mkmatrix($SIZE, $SIZE);
          while ($n--) {
            $mm = mmult($SIZE, $SIZE, $m1, $m2);
          }
          print "{$mm[0][0]} {$mm[2][3]} {$mm[3][2]} {$mm[4][4]}\n";
        }

        matrix(1);""", capfd)
        assert out == "3355 13320 17865 23575\n"

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

    def test_sieve(self, capfd):
        out = self.run("""function sieve($n) {
          $count = 0;
          while ($n-- > 0) {
            $count = 0;
            $flags = range (0,10);
            for ($i=2; $i<11; $i++) {
              if ($flags[$i] > 0) {
                for ($k=$i+$i; $k <= 9; $k+=$i) {
                  $flags[$k] = 0;
                }
                $count++;
              }
            }
          }
          print "Count: $count\n";
        }

        sieve(2);""", capfd)
        assert out == "Count: 5\n"

    def test_strcat(self, capfd):
        out = self.run("""function strcat($n) {
          $str = "";
          while ($n-- > 0) {
            $str .= "hello\n";
          }
          $len = strlen($str);
          print "$len\n";
        }

        strcat(2);""", capfd)
        assert out == "12\n"
