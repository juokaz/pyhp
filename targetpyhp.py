import sys
from rpython.jit.codewriter.policy import JitPolicy
from pyhp.main import run


def main(argv):
    filename = argv[1]
    return run(filename)


def target(driver, args):
    driver.exe_name = 'pyhp-c'
    return main, None


def jitpolicy(driver):
    return JitPolicy()


if __name__ == '__main__':
    main(sys.argv)
