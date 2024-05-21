from verified_agile_hardware.yosys_utils import garnet_to_btor, flatten_garnet
from verified_agile_hardware.garnet_utils import (
    config_garnet,
    remove_config_regs,
    get_garnet_inputs,
    get_garnet_btor_outputs,
)
from verified_agile_hardware.solver import Solver
from verified_agile_hardware.coreir_utils import (
    read_coreir,
    coreir_to_nx,
    nx_to_pdf,
    nx_to_smt,
    pnr_to_nx,
)
from verified_agile_hardware.lake_utils import mem_tile_get_num_valids
import time
import os
import sys
import pono
from .verify_design_top import (
    import_from,
    print_trace,
    flatten,
    set_clk_rst_flush
)

import copy
import json
import argparse
import sys
from pycyclone.io import load_placement
import pycyclone
import pythunder
from archipelago.io import load_routing_result
from archipelago.pnr_graph import (
    RoutingResultGraph,
    construct_graph,
    TileType,
    RouteType,
    TileNode,
    RouteNode,
)


def set_bitstream_cycle_count(solver):
    bvsort16 = solver.create_bvsort(16)


    bmc_equals_6 = solver.create_term(
        solver.ops.Equal, solver.bmc_counter, solver.create_term(6, bvsort16)
    )

    solver.fts.add_invar(
        solver.create_term(solver.ops.Implies, bmc_equals_6, 
            solver.create_term(solver.ops.Equal, solver.cycle_count, solver.create_term(0, bvsort16))
        )
    )

    for name, term in solver.fts.named_terms.items():
        if "cycle_count" in name and not solver.fts.is_next_var(term):
            solver.fts.add_invar(
                solver.create_term(solver.ops.Equal, term, solver.cycle_count)
            )

def set_garnet_inputs(solver, garnet_inputs):

    clk = garnet_inputs["clk"]
    reset = garnet_inputs["reset"]
    flush = garnet_inputs["flush"]
    stall = garnet_inputs["stall"]

    if clk in solver.fts.inputvars:
        solver.fts.promote_inputvar(clk)
    solver.fts.constrain_init(
        solver.create_term(
            solver.ops.Equal, clk, solver.create_term(1, clk.get_sort())
        )
    )
    ite = solver.create_term(
        solver.ops.Ite,
        solver.create_term(
            solver.ops.Equal, clk, solver.create_term(0, clk.get_sort())
        ),
        solver.create_term(1, clk.get_sort()),
        solver.create_term(0, clk.get_sort()),
    )
    solver.fts.assign_next(clk, ite)

    rst_times = [0, 1]
    if reset in solver.fts.inputvars:
        solver.fts.promote_inputvar(reset)
    solver.fts.constrain_init(
        solver.create_term(
            solver.ops.Equal, reset, solver.create_term(1, reset.get_sort())
        )
    )
    solver.fts_assert_at_times(
        reset,
        solver.create_term(1, reset.get_sort()),
        solver.create_term(0, reset.get_sort()),
        rst_times,
    )

    flush_times = [2, 3]
    if flush in solver.fts.inputvars:
        solver.fts.promote_inputvar(flush)
    solver.fts.constrain_init(
        solver.create_term(
            solver.ops.Equal, flush, solver.create_term(0, flush.get_sort())
        )
    )
    solver.fts_assert_at_times(
        flush,
        solver.create_term(1, flush.get_sort()),
        solver.create_term(0, flush.get_sort()),
        flush_times,
    )

    solver.fts.add_invar(
        solver.create_term(solver.ops.Equal, stall, solver.create_term(0, stall.get_sort()))
    )

    for name, term in garnet_inputs.items():
        if "config" in name:
            solver.fts.add_invar(
                solver.create_term(solver.ops.Equal, term, solver.create_term(0, term.get_sort()))
            )


def create_bitstream_property_term(
    solver,
    input_symbols_pnr,
    output_symbols_pnr,
    garnet_inputs,
    garnet_outputs,
    placement,
    input_to_output_cycle_dep
):

    bvsort16 = solver.create_bvsort(16)

    for input_pnr_name, input_symbol_pnr in input_symbols_pnr.items():
        name = input_pnr_name.replace(".out", "")
        assert name in placement, f"{name} not in placement"

        loc = placement[name]

        x = loc[0]
        y = loc[1]
        x_hex = hex(x)[2:]
        y_hex = hex(y)[2:]

        if len(x_hex) == 1:
            x_hex = "0" + x_hex

        if len(y_hex) == 1:
            y_hex = "0" + y_hex

        garnet_name = (
            f"glb2io_{input_symbol_pnr.get_sort().get_width()}_X{x_hex}_Y{y_hex}"
        )

        assert garnet_name in garnet_inputs

        garnet_input = garnet_inputs[garnet_name]

        solver.fts.add_invar(
            solver.create_term(
                solver.ops.Equal,
                input_symbol_pnr,
                garnet_input,
            )
        )

        state_var = solver.create_fts_state_var(input_pnr_name + "_state", input_symbol_pnr.get_sort())
        input_var = solver.create_fts_input_var(input_pnr_name + "_input", input_symbol_pnr.get_sort())

        clk_low = solver.create_term(
            solver.ops.Equal,
            solver.clks[0],
            solver.create_term(0, solver.create_bvsort(1)),
        )

        solver.fts.assign_next(
            state_var,
            solver.create_term(solver.ops.Ite, clk_low, input_var, state_var),
        )

        solver.fts.add_invar(solver.create_term(solver.ops.Equal, state_var, input_symbol_pnr))

    property_term = solver.create_term(True)

    for output_pnr_name, output_symbol_pnr in output_symbols_pnr.items():
        name = output_pnr_name.replace("out.", "")
        assert name in placement

        loc = placement[name]

        x = loc[0]
        y = loc[1]
        x_hex = hex(x)[2:]
        y_hex = hex(y)[2:]

        if len(x_hex) == 1:
            x_hex = "0" + x_hex

        if len(y_hex) == 1:
            y_hex = "0" + y_hex

        garnet_name = (
            f"io2glb_{output_symbol_pnr.get_sort().get_width()}_X{x_hex}_Y{y_hex}"
        )

        assert garnet_name in garnet_outputs, breakpoint()

        garnet_output = garnet_outputs[garnet_name]

        print(output_pnr_name, "matched with", garnet_name)

        property_term = solver.create_term(
            solver.ops.And,
            property_term,
            solver.create_term(
                solver.ops.Equal,
                output_symbol_pnr,
                garnet_output,
            ),
        )

    output_dep_on_input = solver.create_term(
        solver.ops.BVUle,
        solver.bmc_counter,
        solver.create_term(2 * input_to_output_cycle_dep, bvsort16),
    )

    property_term = solver.create_term(
        solver.ops.Or, output_dep_on_input, property_term
    )

    return property_term


def verify_bitstream(
    interconnect, coreir_file, instance_to_instr, pipeline_config_interval, bitstream
):
    file_info = {}
    file_info["port_remapping"] = coreir_file.replace(
        "design_top.json", "design.port_remap"
    )
    app_dir = os.path.dirname(coreir_file)

    solver = Solver()
    solver.file_info = file_info
    solver.app_dir = f"{app_dir}/verification"

    solver.starting_cycle = 0
    solver.max_cycles = 150

    interconnect.pipeline_config_interval = pipeline_config_interval

    bvsort16 = solver.create_bvsort(16)
    bvsort1 = solver.create_bvsort(1)

    if not os.path.exists(solver.app_dir):
        os.mkdir(solver.app_dir)


    # load PnR results
    packed_file = coreir_file.replace("design_top.json", "design.packed")
    placement_file = coreir_file.replace("design_top.json", "design.place")
    routing_file = coreir_file.replace("design_top.json", "design.route")

    netlist, buses = pythunder.io.load_netlist(packed_file)
    id_to_name = pythunder.io.load_id_to_name(packed_file)

    solver.id_to_name = id_to_name

    placement = load_placement(placement_file)
    routing = load_routing_result(routing_file)

    # Construct PnR result graph
    routing_result_graph = construct_graph(
        placement, routing, id_to_name, netlist, 1, 0, 1, False
    )

    nx_pnr = pnr_to_nx(
        routing_result_graph,
        read_coreir(coreir_file.replace("design_top.json", "design_top.json")),
        instance_to_instr,
    )

    _, input_symbols_pnr, output_symbols_pnr = nx_to_smt(
        nx_pnr, interconnect, solver, app_dir
    )

    set_bitstream_cycle_count(solver)

    set_clk_rst_flush(solver)

    # interconnect_def = remove_config_regs(f"{solver.app_dir}/garnet.v", f"{solver.app_dir}/garnet_no_regs.v")

    # flatten_garnet(app_dir=solver.app_dir, garnet_filename=f"{solver.app_dir}/garnet_no_regs.v", garnet_flattened=f"{solver.app_dir}/garnet_flattened.v")

    # config_garnet(interconnect, bitstream, f"{solver.app_dir}/garnet_flattened.v", f"{solver.app_dir}/garnet_configed.v", interconnect_def)

    # garnet_to_btor(app_dir=solver.app_dir, garnet_filename=f"{solver.app_dir}/garnet_configed.v", btor_filename=f"{solver.app_dir}/garnet_configed.btor2")

    solver.read_btor2(f"{solver.app_dir}/garnet_configed.btor2")

    garnet_inputs = get_garnet_inputs(solver)
    garnet_outputs = get_garnet_btor_outputs(
        solver, f"{solver.app_dir}/garnet_configed.btor2"
    )

    set_garnet_inputs(solver, garnet_inputs)

    input_to_output_cycle_dep = solver.first_valid_output + 10


    property_term = create_bitstream_property_term(
        solver,
        input_symbols_pnr,
        output_symbols_pnr,
        garnet_inputs,
        garnet_outputs,
        placement,
        input_to_output_cycle_dep
    )

    prop = pono.Property(solver.solver, property_term)

    btor_solver = solver
    bmc = pono.Bmc(prop, solver.fts, btor_solver.solver)

    check_cycles = solver.max_cycles

    print("First valid output at cycle", solver.first_valid_output)
    print("Running BMC for", check_cycles, "cycles")

    assert (
        check_cycles > solver.first_valid_output
    ), "Check cycles less than first_valid_output"
    start = time.time()
    res = bmc.check_until(check_cycles * 2)
    print(time.time() - start)

    if res is None or res:
        print("\n\033[92m" + "Formal check of mapped application passed" + "\033[0m")

    else:

        vcd_printer = pono.VCDWitnessPrinter(solver.fts, bmc.witness())
        vcd_printer.dump_trace_to_file("/aha/bitstream_verification.vcd")

        waveform_signals = list(garnet_outputs.keys()) + list(output_symbols_pnr.keys())

        symbols = ["bmc_counter", "flush", "reset"]
        symbols += list(input_symbols_pnr.keys())
        # symbols += list(output_symbols_pnr.keys())
        symbols += list(garnet_inputs.keys())
        # symbols += list(garnet_outputs.keys())


        print_trace(solver, bmc, symbols, waveform_signals)


        breakpoint()
