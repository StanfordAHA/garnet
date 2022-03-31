#!/bin/bash
cp $GARNET_HOME/global_buffer/Makefile ./
cp -r $GARNET_HOME/global_buffer/sim ./
cp -r $GARNET_HOME/global_buffer/gls ./
cp -r $GARNET_HOME/global_buffer/testvectors ./

cd outputs

ln -s ../Makefile
ln -s ../sim
ln -s ../gls
ln -s ../testvectors

