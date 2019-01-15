#!/bin/bash

set -x  # echo commands

pytest --codestyle \
       --cov cb \
       --cov common \
       --cov global_controller \
       --cov memory_core \
       --cov pe_core \
       --cov sb \
       --cov simple_cb \
       --cov interconnect \
       --ignore=filecmp.py \
       --ignore=Genesis2/ \
       -v --cov-report term-missing . \
       $@  # Passthrough parameters to pytest command
