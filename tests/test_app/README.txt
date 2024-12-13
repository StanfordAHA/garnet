To run a pointwise test using verilator, in the approved docker
container, you can do the following:

------------------------------------------------------------------------
### Install g++ version 10 and verilator version 5.028.
You can do this by simply running "make setup-verilator" in this directory.

% make -n setup-verilator
    echo "--- MAKE SETUP: Install g++-10, autoconf, bison, help2man"
    yes | (apt update; apt upgrade; apt install g++-10)
    cd /usr/bin; test -e g++ && mv g++ g++.orig; ln -s g++-10 g++

    echo These are missing in docker ATM 
    yes | apt-get install autoconf
    yes | apt-get install bison
    yes | apt-get install help2man

    echo "--- MAKE SETUP: Install verilator 5.028"
    cd /usr/share; test -d verilator || git clone https://github.com/verilator/verilator
    cd /usr/share/verilator; git checkout v5.028
    cd /usr/share/verilator; unset VERILATOR_ROOT; autoconf; ./configure
    cd /usr/share/verilator; unset VERILATOR_ROOT; make -j 24 || echo ERROR
    cd /usr/share/verilator; make clean || echo ERROR cannot clean for some reason i guess
    test -e /usr/local/bin/verilator && mv /usr/local/bin/verilator /usr/local/bin/verilator.orig || echo NOT YET
    cd /usr/local/bin; ln -s /usr/share/verilator/bin/verilator
    verilator --version

------------------------------------------------------------------------
### Run the test.
You can do this by simply running "make pointwise" in this directory.
