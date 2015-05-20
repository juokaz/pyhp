from tests import TestBase


class TestBasic(TestBase):
    def test_running(self):
        out = self.run("""$x = 1;
        print $x;""")
        assert out == "1"

    def test_echo(self):
        out = self.run("""$x = 1;
        echo $x;""")
        assert out == "1"

    def test_running_comments(self):
        out = self.run("""// $x is a variable
        $x = 1;
        print $x;""")
        assert out == "1"

    def test_running_comments_block(self):
        out = self.run("""/*
         * $x is a variable
         */
        $x = 1;
        print $x;""")
        assert out == "1"

    def test_running_assigning_variable_twice(self):
        out = self.run("""$x = 1;
        $x= 5;
        print $x;""")
        assert out == "5"

    def test_running_opening_tag(self):
        out = self.run("""<?php
        $x = 1;
        print $x;""")
        assert out == "1"

    def test_discards_function_result_in_a_loop(self):
        """ if stack is not consumed correctly, this will overflow"""
        out = self.run("""function test() {

        }
        for ($x = 1; $x < 200; $x++) {
            test();
        }""")
        assert out == ""

    def test_discards_function_result(self):
        """ if stack is not consumed correctly, this will overflow"""
        program = "function test() {}"
        for i in range(1, 20):
            program += "test();"
        self.run(program)

    def test_discards_expression_result(self):
        """ if stack is not consumed correctly, this will overflow"""
        program = ""
        for i in range(1, 20):
            program += "1 + 1;"
        self.run(program)

    def test_discards_assignment_result(self):
        """ if stack is not consumed correctly, this will overflow"""
        program = "$i = 1;"
        for i in range(1, 20):
            program += "$i = 2;"
        self.run(program)

    def test_discards_increment_result(self):
        """ if stack is not consumed correctly, this will overflow"""
        program = "$i = 1;"
        for i in range(1, 20):
            program += "$i++;"
        self.run(program)

    def test_discards_print(self):
        """ if stack is not consumed correctly, this will overflow"""
        program = "$i = 1;"
        for i in range(1, 20):
            program += "print $i = 1;"
        self.run(program)
