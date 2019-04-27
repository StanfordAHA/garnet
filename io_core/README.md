In the next CGRA, there will be no I/O pads.
Since we are not limited to the number of I/O pads, we can have as many inputs and outpus we want to.
For this reason, this io_cores are not using tristate.

The function of io_core is nothing but just connecting inputs to outputs.
There is no configuration registers inside io_core.

The reason we have io_core even if we do not have configuration is to make the connection between global buffer and the CGRA fabric more clear.
