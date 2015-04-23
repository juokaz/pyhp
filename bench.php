<?php

$total = 0;

function simple() {
  $a = 0;
  for ($i = 0; $i < 10000; $i++)
    $a++;

  $thisisanotherlongname = 0;
  for ($thisisalongname = 0; $thisisalongname < 10000; $thisisalongname++)
    $thisisanotherlongname++;
}

/*****/

function getmicrotime()
{
  $t = gettimeofday();
  return ($t['sec'] + $t['usec'] / 1000000);
}

function start_test()
{
    //ob_start();
  return getmicrotime();
}

function end_test($start, $name)
{
  global $total;
  $end = getmicrotime();
 // ob_end_clean();
  $total += $end-$start;
  $num = number_format($end-$start,3);
  $pad = str_repeat(" ", 24-strlen($name)-strlen($num));

  echo $name.$pad.$num."\n";
  //  ob_start();
  return getmicrotime();
}

function total()
{
  global $total;
  $pad = str_repeat("-", 24);
  echo $pad."\n";
  $num = number_format($total,3);
  $pad = str_repeat(" ", 24-strlen("Total")-strlen($num));
  echo "Total".$pad.$num."\n";
}

$t0 = start_test();
$t = $t0;
simple();
$t = end_test($t, "simple");
total($t0, "Total");
