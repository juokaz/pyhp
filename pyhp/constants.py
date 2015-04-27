from rpython.rlib.rsre.rsre_re import compile


VARIABLENAME = r"\$[a-zA-Z_][a-zA-Z0-9_]*"

# array index regex matching the index and the brackets
ARRAYINDEX = r"\[(?:[0-9]+|%s)\]" % VARIABLENAME

# match variables and array access
VARIABLE = r"(%s(?:%s)*)" % (VARIABLENAME, ARRAYINDEX)
CURLYVARIABLE = compile(r"{?" + VARIABLE + "}?")

ARRAYINDEX = compile(r"\[([0-9]+|%s)\]" % VARIABLENAME)
