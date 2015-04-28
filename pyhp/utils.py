import os


def printf(str, *args):
    """ Default `print` operation adds a newline """
    # 1 here represents stdout
    os.write(1, str)

from rpython.rlib import jit
from rpython.rlib.rfloat import formatd
from rpython.rlib.unroll import unrolling_iterable


FORMAT_CHARS = unrolling_iterable([
    "s", "d", "f"
])


class StringFormatter(object):
    """ From https://github.com/topazproject/topaz"""
    def __init__(self, fmt, items_w):
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
            while self.fmt[i].isdigit():
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
        return ''.join(result_w)

    def _fmt_num(self, num, width):
        return (width - len(num)) * "0" + num

    def fmt_s(self, w_item, width):
        return w_item.str()

    def fmt_d(self, w_item, width):
        num = w_item.get_int()
        return self._fmt_num(str(num), width)

    def fmt_f(self, w_item, width):
        num = w_item.to_number()
        return self._fmt_num(formatd(num, "f", width), width)
