from tests import TestBase

class TestMain(TestBase):
    def test_running(self, capfd):
        out = self.run("""$x = 1;
        print $x;""", capfd)
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
