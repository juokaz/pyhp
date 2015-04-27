from rpython.rlib.rsre.rsre_re import compile


escapes = [
    r'\n',
    r'\r',
    r'\f',
    r'\v',
    r'\ ',
    r'\t',
    r"\'",
    r'\b',
    r'\"',
    r'\\',
    r'\u']  # don't know what to do with these

codes = [
    '\n',
    '\r',
    '\f',
    '\v',
    '\ ',
    '\t',
    "'",
    "\b",
    '"',
    '\\',
    'u']

escapedict = dict(zip(codes, escapes))
unescapedict = dict(zip(escapes, codes))


VARIABLENAME = r"\$[a-zA-Z_][a-zA-Z0-9_]*"

# array index regex matching the index and the brackets
ARRAYINDEX = r"\[(?:[0-9]+|%s)\]" % VARIABLENAME

# match variables and array access
VARIABLE = r"(%s(?:%s)*)" % (VARIABLENAME, ARRAYINDEX)
CURLYVARIABLE = compile(r"{?" + VARIABLE + "}?")

ARRAYINDEX = compile(r"\[([0-9]+|%s)\]" % VARIABLENAME)
