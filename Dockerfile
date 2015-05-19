FROM 32bit/ubuntu:14.04

MAINTAINER Juozas Kaziukenas <juozas@juokaz.com>

RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update -y \
    && apt-get install -y --no-install-recommends \
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
    && wget -q -O - https://bitbucket.org/pypy/pypy/downloads/pypy-2.5.1-linux.tar.bz2 | tar jx \
    && ln -s /tmp/pypy-2.5.1-linux/bin/pypy /usr/local/bin/pypy


RUN cd /tmp \
    && wget -q -O - https://bitbucket.org/pypy/pypy/downloads/pypy-2.5.1-src.tar.bz2 | tar jx

RUN pip install pytest \
    && pip install pytest-cov \
    && pip install flake8 \
    && pip install mock
