from rpython.rlib import jit
from rpython.rlib.rfloat import formatd
from rpython.rlib.unroll import unrolling_iterable

FORMAT_CHARS = unrolling_iterable([
    "s", "d", "f"
])


class StringFormatter(object):
    """ From https://github.com/topazproject/topaz"""
    def __init__(self, fmt, items_w):
        assert isinstance(fmt, unicode)
        self.fmt = fmt
        self.items_w = items_w
        self.item_index = 0

    @jit.look_inside_iff(lambda self: jit.isconstant(self.fmt))
    def format(self):
        i = 0
        result_w = []
        while True:
            start = i
            while i < len(self.fmt):
                if self.fmt[i] == "%":
                    break
                i += 1
            else:
                result_w.append(self.fmt[start:i])
                break
            result_w.append(self.fmt[start:i])
            i += 1
            if self.fmt[i] == '.':  # ignore dots TODO
                i += 1
            width = 0
            while self.fmt[i] in [unicode(str(s)) for s in range(0, 9)]:
                width = width * 10 + (ord(self.fmt[i]) - ord("0"))
                i += 1
            format_char = self.fmt[i]
            w_item = self.items_w[self.item_index]
            self.item_index += 1
            i += 1
            for c in FORMAT_CHARS:
                if c == format_char:
                    w_res = getattr(self, "fmt_" + c)(w_item, width)
                    result_w.append(w_res)
                    break
            else:
                raise NotImplementedError(format_char)
        return u''.join(result_w)

    def _fmt_num(self, num, width):
        return (width - len(num)) * u"0" + num

    def fmt_s(self, w_item, width):
        return w_item.str()

    def fmt_d(self, w_item, width):
        num = w_item.str()
        return self._fmt_num(num, width)

    def fmt_f(self, w_item, width):
        num = w_item.to_number()
        return self._fmt_num(unicode(formatd(num, "f", width)), width)

from rpython.rlib.objectmodel import enforceargs
from rpython.rlib import runicode


@enforceargs(unicode)
def string_unquote(string):
    s = string
    single_quotes = True
    if s.startswith('"'):
        assert s.endswith('"')
        single_quotes = False
    else:
        assert s.startswith("'")
        assert s.endswith("'")
    s = s[:-1]
    s = s[1:]

    return s, single_quotes


@enforceargs(str)
def decode_str_utf8(string):
    result, consumed = runicode.str_decode_utf_8(string, len(string), "strict",
                                                 True)
    return result


@enforceargs(unicode)
def string_unescape(string):
    s = string
    size = len(string)

    from rpython.rlib.rstring import UnicodeBuilder

    if size == 0:
        return u''

    builder = UnicodeBuilder(size)
    pos = 0
    while pos < size:
        ch = s[pos]

        # Non-escape characters are interpreted as Unicode ordinals
        if ch != '\\':
            builder.append(unichr(ord(ch)))
            pos += 1
            continue

        # - Escapes
        pos += 1
        if pos >= size:
            message = u"\\ at end of string"
            raise Exception(message)

        ch = s[pos]
        pos += 1
        # \x escapes
        if ch == '\n':
            pass
        elif ch == '\\':
            builder.append(u'\\')
        elif ch == '\'':
            builder.append(u'\'')
        elif ch == '\"':
            builder.append(u'\"')
        elif ch == 'b':
            builder.append(u'\b')
        elif ch == 'f':
            builder.append(u'\f')
        elif ch == 't':
            builder.append(u'\t')
        elif ch == 'n':
            builder.append(u'\n')
        elif ch == 'r':
            builder.append(u'\r')
        elif ch == 'v':
            builder.append(u'\v')
        elif ch == 'a':
            builder.append(u'\a')
        elif '0' <= ch <= '7':
            x = ord(ch) - ord('0')
            if pos < size:
                ch = s[pos]
                if '0' <= ch <= '7':
                    pos += 1
                    x = (x << 3) + ord(ch) - ord('0')
                    if pos < size:
                        ch = s[pos]
                        if '0' <= ch <= '7':
                            pos += 1
                            x = (x << 3) + ord(ch) - ord('0')
            builder.append(unichr(x))
        # hex escapes
        # \xXX
        else:
            builder.append(unichr(ord(ch)))

    return builder.build()
