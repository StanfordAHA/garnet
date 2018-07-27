from common.genesis_wrapper import GenesisWrapper
from common.generator_interface import GeneratorInterface


interface = GeneratorInterface()\
            .register("width", int, 16)\
            .register("num_tracks", int, 10)\
            .register("feedthrough_outputs", str, "1"*10)\
            .register("has_constant", int, 0)\
            .register("default_value", int, 0)

cb_wrapper = GenesisWrapper(interface, "cb", ["cb/genesis/cb.vp"])

"""
This program generates the verilog for the connect box and parses it into a
Magma circuit. The circuit declaration is printed at the end of the program.
"""
if __name__ == "__main__":
    # These functions are unit tested directly, so no need to cover them
    cb_wrapper.main()  # pragma: no cover
