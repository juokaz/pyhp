<?php

$count = 0;
$x = 0;
$y = 1;

print $x;
print ' - ';
print $y;

while($count < 90) {
    $z = $x + $y;
    print $z;
    print ' - ';
    $x = $y;
    $y = $z;
    $count = $count + 1;
}
