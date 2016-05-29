FROM ubuntu:16.04

MAINTAINER Juozas Kaziukenas <juozas@juokaz.com>

RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update -y \
    && apt-get install -y --no-install-recommends \
        php7.0-cli \
        ca-certificates \
        git-core \
        wget \
        libffi-dev \
        pkg-config \
        python-dev \
        python-pip \
        python-setuptools \
        build-essential \
    && apt-get clean

RUN cd /tmp \
    && wget -q -O - https://bitbucket.org/pypy/pypy/downloads/pypy-5.1.1-linux64.tar.bz2 | tar jx \
    && ln -s /tmp/pypy-5.1.1-linux64/bin/pypy /usr/local/bin/pypy

RUN cd /tmp \
    && wget -q -O - https://bitbucket.org/pypy/pypy/downloads/pypy-5.1.1-src.tar.bz2 | tar jx

RUN pip install pytest \
    && pip install pytest-cov \
    && pip install flake8 \
    && pip install mock
