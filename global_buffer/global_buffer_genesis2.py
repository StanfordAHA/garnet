import magma
from gemstone.common.genesis_wrapper import GenesisWrapper
from gemstone.common.generator_interface import GeneratorInterface

"""
Defines the global buffer using genesis2.

Example usage:
    >>> glb = global_buffer.generator()()

"""
interface = GeneratorInterface()\
    .register("num_banks", int, 32) \
    .register("num_io", int, 8) \
    .register("num_cfg", int, 8) \
    .register("bank_addr_width", int, 17) \
    .register("glb_addr_width", int, 32) \
    .register("bank_data_width", int, 64) \
    .register("cgra_data_width", int, 16) \
    .register("glb_config_reg_width", int, 8) \
    .register("glb_config_tile_width", int, 8) \
    .register("glb_config_feature_width", int, 8) \
    .register("cfg_addr_width", int, 32) \
    .register("cfg_data_width", int, 32)

type_map = {
    "clk": magma.In(magma.Clock),
    "reset": magma.In(magma.AsyncReset),
}

param_mapping = {"num_banks": "num_banks",
                 "num_io": "num_io_channels",
                 "num_cfg": "num_cfg_channels",
                 "cfg_addr_width": "config_addr_width",
                 "cfg_data_width": "config_data_width"}

glb_wrapper = GenesisWrapper(
    interface, "global_buffer", [
        "global_buffer/genesis/global_buffer.svp",
        "global_buffer/genesis/global_buffer_int.svp",
        "global_buffer/genesis/memory_bank.svp",
        "global_buffer/genesis/cfg_bank_interconnect.svp",
        "global_buffer/genesis/cfg_controller.svp",
        "global_buffer/genesis/bank_controller.svp",
        "global_buffer/genesis/host_bank_interconnect.svp",
        "global_buffer/genesis/addrgen_bank_interconnect.svp",
        "global_buffer/genesis/address_generator.svp",
        "global_buffer/genesis/glbuf_memory_core.svp",
        "global_buffer/genesis/memory.svp",
        "global_buffer/genesis/sram_gen.svp",
        "global_buffer/genesis/sram_controller.svp"
    ], system_verilog=True, type_map=type_map)

if __name__ == "__main__":
    """
    This program generates the verilog for the global buffer and parses
    it into a Magma circuit. The circuit declaration is printed at the
    end of the program.
    """
    # These functions are unit tested directly, so no need to cover them
    glb_wrapper.main(param_mapping=param_mapping)  # pragma: no cover
