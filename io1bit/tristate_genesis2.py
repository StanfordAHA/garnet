from common.genesis_wrapper import GenesisWrapper, default_type_map
from common.generator_interface import GeneratorInterface

interface = GeneratorInterface()

tristate_wrapper = GenesisWrapper(interface, "tristate",
                                  ["io1bit/genesis/tristate.vp"],
                                  type_map=default_type_map)

"""
This program generates the verilog for the tristate in IO tile and parses it
into a Magma circuit. The circuit declaration is printed at the end of the
program.
"""
if __name__ == "__main__":
    tristate_wrapper.main()
