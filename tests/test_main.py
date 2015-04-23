from tests import TestBase

class TestMain(TestBase):
    def test_running(self, capfd):
        out = self.run("""$x = 1;
        print $x;""", capfd)
        assert out == "1"

    def test_echo(self, capfd):
        out = self.run("""$x = 1;
        echo $x;""", capfd)
        assert out == "1"

    def test_running_comments(self, capfd):
        out = self.run("""// $x is a variable
        $x = 1;
        print $x;""", capfd)
        assert out == "1"

    def test_running_comments_block(self, capfd):
        out = self.run("""/*
         * $x is a variable
         */
        $x = 1;
        print $x;""", capfd)
        assert out == "1"

    def test_running_assigning_variable_twice(self, capfd):
        out = self.run("""$x = 1;
        $x= 5;
        print $x;""", capfd)
        assert out == "5"

    def test_running_opening_tag(self, capfd):
        out = self.run("""<?php
        $x = 1;
        print $x;""", capfd)
        assert out == "1"

    def test_discards_function_result_in_a_loop(self, capfd):
        out = self.run("""function test() {

        }
        for ($x = 1; $x < 200; $x++) {
            test();
        }""", capfd)
        assert out == ""

    def test_discards_function_result(self, capfd):
        out = self.run("""function test() {

        }
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test();
        test(); test(); test(); test(); test(); """, capfd)
        assert out == ""

    def test_discards_expression_result(self, capfd):
        out = self.run("""1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1;
        1+1; 1+1; 1+1; 1+1; 1+1; 1+1; 1+1; """, capfd)
        assert out == ""

    def test_discards_assignment_result(self, capfd):
        out = self.run("""$i = 1;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;
        $i++; $i++; $i++; $i++; $i++;  """, capfd)
        assert out == ""
