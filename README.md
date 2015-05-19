# PyHP

PyHP is an (incomplete!) implementation of the PHP language using the
[RPython](http://pypy.org) technology. It uses JIT transformer provided by the
RPython library to achieve good performance.

PyHP stands for Python + PHP, as RRpython is a subset of the Python language.

Highly unstable and work in progress.

[HippyVM](https://github.com/hippyvm/hippyvm) is too built on top of RPython,
and is a complete, working implementation.

## Features

- all variable types like int, float, string, array, iterator
- if, while, for, foreach statements
- functions
- pass by value or by reference to a function
- global variables in function blocks using `global`
- global constants using `define()`
- (incomplete) standard library functions
- unicode support for function/variable names and string values. PHP 6 compatible!

## Project structure

- `main.py` - main entry point
- `sourceparcer.py` - parses a given PHP file using the `grammar.txt` definition,
and produces an AST tree consisting of `operations.py` nodes
- `bytecode.py` - turns the AST tree produced by `sourceparcer.py` into bytecode
by calling `compile()` on the tree. Produces a `ByteCode` instance consisting of
`opcodes.py` nodes
- `frame.py` - execution frame. Contains the stack and the variables/functions map
for the function or the global program. A frame instance is passed to `execute`
method of a `Interpreter` instance as the only parameter
- `interpreter.py` - loops over a list of bytecodes and evaluates a `opcodes.py`
handler
- `grammar.txt` - EBNF PHP grammar used by `sourceparcer.py`

Additional files:
- `operations.py` - AST tree nodes
- `opcodes.py` - class per each opcode. Each opcode has a `eval(frame)` method which gets
called by the `Interpreter.execute()` method
- `symbols.py` - contains an optimized `Map` class used for symbols map in `scopes.py`
- `stdlib.py` - various PHP standard library methods like `strlen`
- `datatypes.py` - all datatypes' box classes used to store the variables,
like int, float, array, etc.

## Building

### Building the interpreter

    docker pull juokaz/pyhp
    make build

Or to build without JIT support

    make build-nojit

### Running the benchmark

    make bench

Or run any PHP file

    ./build/pyhp bench.php

### Starting the web server

    ./build/pyhp --server 8080

Accessible through http://localhost:8080/bench.php.

### Printing the bytecode

    ./build/pyhp --bytecode bench.php

### Printing the AST tree

    ./build/pyhp --ast bench.php

### Debugging the interpreter

    PYPYLOG=jit-log-opt:jit.txt ./build/pyhp bench.php

Plot the trace as a graph

    PYTHONPATH=$PYTHONPATH:/home/vagrant/pypy-src/ python ~/pypy-src/rpython/tool/logparser.py draw-time jit.txt --mainwidth=8000 filename.png

### Running the tests

    make tests

Or to run with coverage information

    make tests-cov

### Building the docker container

    docker build -t juokaz/pyhp .

## Attributions and inspirations

[JavaScript on top of RPython](https://bitbucket.org/pypy/lang-js/src/de89ec32a7dc?at=default)

[Example interpreter](https://bitbucket.org/pypy/example-interpreter/src/a00d0f9c36f1?at=default)

[Pascal on top of RPython](https://github.com/WarPie/Pascal)

[HippyVM - php on top of RPython](https://github.com/hippyvm/hippyvm)
