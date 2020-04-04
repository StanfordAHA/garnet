#!/bin/bash

garnet: rdl_models/garnet.rdl ordt_params/garnet.parms
	java -jar Ordt.jar -parms ordt_params/garnet.parms -systemverilog output/ rdl_models/garnet.rdl

glb: rdl_models/glb.rdl ordt_params/glb.parms
	rdl_prepro.pl rdl_models/glb.rdl
	java -jar Ordt.jar -parms ordt_params/glb.parms -systemverilog output/ rdl_models/glb.rdl.pp.final

