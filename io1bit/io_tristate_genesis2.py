from common.genesis_wrapper import GenesisWrapper, default_type_map
from common.generator_interface import GeneratorInterface

interface = GeneratorInterface()

io_tristate_wrapper = GenesisWrapper(interface, "io_tristate",
                                ["io1bit/genesis/io_tristate.vp"],
                                type_map=default_type_map)

"""
This program generates the verilog for the tristate in IO tile and parses it into a
Magma circuit. The circuit declaration is printed at the end of the program.
"""
if __name__ == "__main__":
    io_tristate_wrapper.main()
