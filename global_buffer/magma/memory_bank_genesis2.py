import magma
from gemstone.common.genesis_wrapper import GenesisWrapper
from gemstone.common.generator_interface import GeneratorInterface

"""
Defines the global buffer's i/o address generator using genesis2.

Example usage:
    >>> mem_bank = memory_bank.generator()()

"""
interface = GeneratorInterface()

type_map = {
    "clk": magma.In(magma.Clock),
    "reset": magma.In(magma.AsyncReset),
}

memory_bank_wrapper = GenesisWrapper(
    interface, "memory_bank", [
        "global_buffer/genesis/memory_bank.svp",
    ], system_verilog=True, type_map=type_map)

if __name__ == "__main__":
    """
    This program generates the verilog for the memory bank and parses
    it into a Magma circuit. The circuit declaration is printed at the
    end of the program.
    """
    # These functions are unit tested directly, so no need to cover them
    memory_bank_wrapper.main()  # pragma: no cover
