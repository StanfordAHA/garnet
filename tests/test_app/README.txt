To run a quick test using verilator, you can do the following
(assuming you are in the context of an approved docker container).

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

You can run the test by simply doing "make gaussian."  Gaussian builds
a 4x16 CGRA grid and takes about 35 minutes in the docker container.

For a longer test, you can run "make pointwise", which builds a 28x16
grid and takes more like 2.5 hours.

% make -n gaussian
    aha garnet --width 4 --height 16 --verilog --use_sim_sram --glb_tile_mem_size 128
    cd /aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/gaussian; make clean
    aha map apps/gaussian --chain
    aha pnr apps/gaussian --width 4 --height 16
    TOOL=VERILATOR stdbuf -oL -eL aha test apps/gaussian