import magma
from gemstone.common.genesis_wrapper import GenesisWrapper
from gemstone.common.generator_interface import GeneratorInterface


interface = GeneratorInterface()\
    .register("cfg_bus_width", int, 32)\
    .register("cfg_addr_width", int, 32)\
    .register("cfg_op_width", int, 5)\
    .register("soc_addr", int, 12)

type_map = {
    "clk_in": magma.In(magma.Clock),
    "clk_out": magma.Out(magma.Clock),
    "tck": magma.In(magma.Clock),
    "reset_in": magma.In(magma.AsyncReset),
    "reset_out": magma.Out(magma.AsyncReset),
    "trst_n": magma.In(magma.AsyncReset),
}
gc_wrapper = GenesisWrapper(interface,
                            "global_controller",
                            ["global_controller/genesis/global_controller.svp",
                             "global_controller/genesis/jtag.svp",
                             "global_controller/genesis/tap.svp",
                             "global_controller/genesis/flop.svp",
                             "global_controller/genesis/cfg_and_dbg.svp"],
                            system_verilog=True, type_map=type_map)

if __name__ == "__main__":
    """
    This program generates the verilog for the global controller and parses it
    into a Magma circuit. The circuit declaration is printed at the end of the
    program.
    """
    # These functions are unit tested directly, so no need to cover them
    gc_wrapper.main()  # pragma: no cover
