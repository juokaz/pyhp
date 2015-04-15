Building the interpreter

    cd /var/www/pyhp
    rpython targetpyhp.py

Running the interpreter

    ./targetpyhp-c example.php

Run tests

    PYTHONPATH=$PYTHONPATH:/home/vagrant/pypy-src/ py.test tests
