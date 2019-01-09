from common.genesis_wrapper import GenesisWrapper, default_type_map
from common.generator_interface import GeneratorInterface

interface = GeneratorInterface()\
            .register("io_group", int, 0)\
            .register("side", int, 0)

io1bit_wrapper = GenesisWrapper(interface, "io1bit",
                                ["io1bit/genesis/io1bit.vp"],
                                type_map=default_type_map)

"""
This program generates the verilog for the io1bit tile and parses it into a
Magma circuit. The circuit declaration is printed at the end of the program.
"""
if __name__ == "__main__":
    io1bit_wrapper.main()
