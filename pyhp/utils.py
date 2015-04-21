import os


def printf(str, *args):
    """ Default `print` operation adds a newline """
    # 1 here represents stdout
    os.write(1, str)


# String methods, because pypy string methods work differently than python
def find(str, sub, pos=0):
    assert pos >= 0
    for i in range(pos, len(str)):
        if str[i:i + len(sub)] == sub:
            return i
    return -1


def find_all(str, sub):
    start = 0
    res = []
    while True:
        start = find(str, sub, start)
        if start == -1:
            return res
        res.append(start)
        start += len(sub)
    return res


def replace(text, substr, repstr):
    subs = find_all(text, substr)
    if len(subs) == 0:
        return text
    result = ''
    j = 0
    for i in subs:
        assert i >= 0
        assert j >= 0
        result += text[j:i]
        result += repstr
        j = i+len(substr)
        result += text[j:]
    return result
