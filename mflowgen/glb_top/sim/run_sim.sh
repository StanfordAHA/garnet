#!/bin/bash
make -C $GARNET_HOME/global_buffer run

cp $GARNET_HOME/global_buffer/vcs.log outputs/sim.log
