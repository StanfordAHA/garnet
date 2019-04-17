import magma
from gemstone.common.genesis_wrapper import GenesisWrapper
from gemstone.common.generator_interface import GeneratorInterface

"""
Defines the global buffer using genesis2.

Example usage:
    >>> glb = global_buffer_wrapper.generator()()

"""
interface = GeneratorInterface()\
    .register("num_banks", int, 32) \
    .register("bank_addr_width", int, 16) \
    .register("bank_data_width", int, 64) \
    .register("top_config_addr_width", int, 32) \
    .register("top_config_data_width", int, 32)

type_map = {
    "clk": magma.In(magma.Clock),
    "reset": magma.In(magma.AsyncReset),
}

global_buffer_wrapper = GenesisWrapper(
    interface, "global_buffer", [
        "global_buffer/genesis/global_buffer.svp",
        "global_buffer/genesis/memory_bank.svp"
    ], system_verilog=True, type_map=type_map)

if __name__ == "__main__":
    """
    This program generates the verilog for the global buffer and parses
    it into a Magma circuit. The circuit declaration is printed at the
    end of the program.
    """
    # These functions are unit tested directly, so no need to cover them
    global_buffer_wrapper.main()  # pragma: no cover
