from tests import TestBase


class TestMain(TestBase):
    def test_bytecode(self):
        bytecode = self.bytecode("""function a($x) {
            print $x;
        }
        $x = 1;
        print $x;""")
        assert str(bytecode) == """Function a($x):
0: LOAD_VAR 0, $x
1: PRINT
2: RETURN

/tmp/example.php:
0: DECLARE_FUNCTION a
1: LOAD_INTVAL 1
2: ASSIGN 0, $x
3: DISCARD_TOP
4: LOAD_VAR 0, $x
5: PRINT
6: RETURN"""

    def test_ast(self):
        ast = self.ast("""function a($x) {
            print $x;
        }
        $x = 1;
        print $x;""")
        assert str(ast) == """Program (
\tSourceElements (
\t\tFunction (a,
\t\t\tSourceElements (
\t\t\t\tPrint (VariableIdentifier (0, $x))
\t\t\t)
\t\t)
\t\tExprStatement (AssignmentOperation (VariableIdentifier (0, $x), =, ConstantInt 1))
\t\tPrint (VariableIdentifier (0, $x))
\t)
)"""  # NOQA

    def test_running(self, capfd):
        out = self.run("""$x = 1;
        print $x;""", capfd)
        assert out == "1"

    def test_running_return(self, capfd):
        out = self.run_return("""$x = 1;
        print $x;""")
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
        """ if stack is not consumed correctly, this will overflow"""
        out = self.run("""function test() {

        }
        for ($x = 1; $x < 200; $x++) {
            test();
        }""", capfd)
        assert out == ""

    def test_discards_function_result(self, capfd):
        """ if stack is not consumed correctly, this will overflow"""
        program = "function test() {}"
        for i in range(1, 20):
            program += "test();"
        self.run(program, capfd)

    def test_discards_expression_result(self, capfd):
        """ if stack is not consumed correctly, this will overflow"""
        program = ""
        for i in range(1, 20):
            program += "1 + 1;"
        self.run(program, capfd)

    def test_discards_assignment_result(self, capfd):
        """ if stack is not consumed correctly, this will overflow"""
        program = "$i = 1;"
        for i in range(1, 20):
            program += "$i = 2;"
        self.run(program, capfd)

    def test_discards_increment_result(self, capfd):
        """ if stack is not consumed correctly, this will overflow"""
        program = "$i = 1;"
        for i in range(1, 20):
            program += "$i++;"
        self.run(program, capfd)

    def test_discards_print(self, capfd):
        """ if stack is not consumed correctly, this will overflow"""
        program = "$i = 1;"
        for i in range(1, 20):
            program += "print $i = 1;"
        self.run(program, capfd)
