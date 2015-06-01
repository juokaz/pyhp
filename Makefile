#
# Makefile for building various parts of pyhp.
#
# The recommended approach is to use the pre-built docker image for the
# build environment, available via:
#
#     docker build -t juokaz/pyhp .
#
# If you'd like to use your own versions of these dependencies you
# will need to install:
#
#   * a 32-bit pypy interpreter, for running the build
#   * a 32-bit cpython intereter, for running the tests
#   * 32-bit development libraries for "libffi" and "libgc"
#
# You can tweak the makefile variables below to point to such an environment.
#


# This runs the dockerized build commands as if they were in the current
# directory, with write access to the current directory.

RPYTHON = /tmp/pypy-2.6.0-src
RPYTHON_BIN = $(RPYTHON)/rpython/bin/rpython

DOCKER_IMAGE = juokaz/pyhp

DOCKER_ARGS = -ti -v $(CURDIR):$(CURDIR) -w $(CURDIR) -e "IN_DOCKER=1" -e "PYTHONPATH=$$PYTHONPATH:$(RPYTHON)"

ifeq ($(CIRCLECI),)
    DOCKER_ARGS += --rm
endif

ifeq ($(IN_DOCKER), 1)
    DOCKER =
else
    DOCKER = docker run $(DOCKER_ARGS) $(DOCKER_IMAGE)
endif

# Change these variables if you want to use a custom build environment.
# They must point to a 32-bit python executable and a 32-bit pypy executable.

PYTHON = $(DOCKER) python
PYPY = $(DOCKER) pypy

# Build targets

.PHONY: build
build: ./build/pyhp

./build/pyhp:
	mkdir -p build
	$(PYPY) $(RPYTHON_BIN) -Ojit  --output=./build/pyhp targetpyhp.py

# This builds a version of pypy.js without its JIT, which is useful for
# investigating the size or performance of the core interpreter.
# Emits the `-Ojit`. Speeds up the build process by 5x, but the produced
# interpreter runs much slower.

.PHONY: build-nojit
build-nojit: ./build/pyhp-nojit

./build/pyhp-nojit:
	mkdir -p build
	$(PYPY) $(RPYTHON_BIN) --opt=2  --output=./build/pyhp-nojit targetpyhp.py

# Convenience target to launch a shell in the dockerized build environment.

shell:
	$(DOCKER) /bin/bash

# Run tests

.PHONY: tests
tests:
	$(DOCKER) py.test tests

tests-cov:
	$(DOCKER) py.test --cov pyhp --cov-report html --cov-report term tests

flake8:
	$(DOCKER) flake8 pyhp tests

bench: ./build/pyhp
	$(DOCKER) ./build/pyhp bench.php
