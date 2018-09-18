from common.genesis_wrapper import GenesisWrapper
from common.generator_interface import GeneratorInterface


"""
Defines the pe using genesis2.


Example usage:
    >>> pe = pe_wrapper.generator()()
"""
interface = GeneratorInterface()\
            .register("reg_inputs", int, 1)\
            .register("reg_out", int, 0)\
            .register("use_add", int, 2)\
            .register("use_cntr", int, 1)\
            .register("use_bool", int, 1)\
            .register("use_shift", int, 1)\
            .register("mult_mode", int, 2)\
            .register("use_div", int, 0)\
            .register("is_msb", int, 0)\
            .register("en_double", int, 0)\
            .register("en_opt", int, 1)\
            .register("en_trick", int, 0)\
            .register("use_abs", int, 1)\
            .register("use_max_min", int, 1)\
            .register("use_relu", int, 0)\
            .register("get_carry", int, 1)\
            .register("debug", int, 0)\
            .register("use_flip", int, 0)\
            .register("use_acc", int, 1)\
            .register("en_ovfl", int, 1)\
            .register("en_debug", int, 1)\
            .register("lut_inps", int, 3)\
            .register("reg_cnt", int, 1)

type_map = {
    "clk": magma.In(magma.Clock),
}

pe_core_wrapper = GenesisWrapper(
    interface, "test_pe", [
        "pe_core/genesis/test_pe_red.svp",
        "pe_core/genesis/test_pe_dual.vpf",
        "pe_core/genesis/test_pe_comp.svp",
        "pe_core/genesis/test_pe_comp_dual.svp",
        "pe_core/genesis/test_cmpr.svp",
        "pe_core/genesis/test_pe.svp",
        "pe_core/genesis/test_mult_add.svp",
        "pe_core/genesis/test_full_add.svp",
        "pe_core/genesis/test_lut.svp",
        "pe_core/genesis/test_opt_reg.svp",
        "pe_core/genesis/test_simple_shift.svp",
        "pe_core/genesis/test_shifter.svp",
        "pe_core/genesis/test_debug_reg.svp",
        "pe_core/genesis/test_opt_reg_file.svp"
    ], system_verilog=True, type_map=type_map)

if __name__ == "__main__":
    """
    This program generates the verilog for the pe and parses it into a
    Magma circuit. The circuit declaration is printed at the end of the
    program.
    """
    # These functions are unit tested directly, so no need to cover them
    pe_core_wrapper.main()  # pragma: no cover
