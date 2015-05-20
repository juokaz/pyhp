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
1: LOAD_CONSTANT 0
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
        code = """print 'Hello world';"""
        filename = self.store(code)

        code = self.main(['', filename])
        assert code == 0
        out, err = capfd.readouterr()
        assert out == "Hello world"

    def test_running_not_found(self, capfd):
        code = self.main(['', 'file.php'])
        assert code == 1
        out, err = capfd.readouterr()
        assert out == "File not found file.php\n"

    def test_running_no_filename(self, capfd):
        code = self.main([''])
        assert code == 1
        out, err = capfd.readouterr()
        assert out == "Required parameter filename missing\n"
