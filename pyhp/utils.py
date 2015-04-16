import os


def printf(str, *args):
    """ Default `print` operation adds a newline """
    # 1 here represents stdout
    os.write(1, str)
