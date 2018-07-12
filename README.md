This repository contains the files for a simple CGRA module: the connect box. In this repo you will find:
* A python functional model for the connect box (`cb_functional_model.py`)
* The original Genesis2 source for the connect box (`cb.vp`), along with scripts to generate Verilog from the Genesis2 file (`python cb_wrapper_main.py <args>` generates the file `genesis_verif/cb.v`)
* An implementation of the connect box in Magma
* Test harnesses to regress the Magma implementation against the original Genesis2 implementation (as well as against the functional model).
