from verified_agile_hardware.coreir_utils import (
    read_coreir,
    coreir_to_nx,
    nx_to_pdf,
    nx_to_smt,
    pnr_to_nx,
)
from verified_agile_hardware.lake_utils import mem_tile_get_num_valids
from memory_core.memtile_util import LakeCoreBase
import time
import os
import pono
from simple_colors import *
import re
from tabulate import tabulate
from .verify_design_top import (
    import_from,
    print_trace,
    flatten,
    set_clk_rst_flush,
    synchronize_cycle_counts,
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
from verified_agile_hardware.solver import Solver, Rewriter
import smt_switch as ss


def set_pnr_inputs(
    solver, input_symbols_coreir, input_symbols_pnr, bvsort16, id_to_name
):

    # Map pnr symbols to names
    input_pnr_names_to_symbols = {}
    for pnr_symbol_name, pnr_symbol in input_symbols_pnr.items():
        input_pnr_id = pnr_symbol_name.split(".")[0]
        input_pnr_name = id_to_name[input_pnr_id]
        input_pnr_names_to_symbols[input_pnr_name] = pnr_symbol

    # set each input symbol in coreir and pnr graphs equal
    for input_coreir_name in input_symbols_coreir:
        # find the matching pnr input
        input_coreir_name_sliced = input_coreir_name.split(".")[1]
        for pnr_idx, (input_pnr_name, input_pnr_symbol) in enumerate(
            input_pnr_names_to_symbols.items()
        ):
            if input_coreir_name_sliced in input_pnr_name:
                # map coreir name and pnr ID back to nodes
                input_coreir = input_symbols_coreir[input_coreir_name]
                input_pnr_short = solver.fts.make_term(
                    ss.Op(
                        ss.primops.Extract, input_coreir.get_sort().get_width() - 1, 0
                    ),
                    input_pnr_symbol,
                )

                # PnR inputs are delayed by 1 cycle

                input_coreir_d0 = solver.create_fts_state_var(
                    input_coreir_name + "_d0_" + str(pnr_idx), input_coreir.get_sort()
                )
                input_coreir_d1 = solver.create_fts_state_var(
                    input_coreir_name + "_d1_" + str(pnr_idx), input_coreir.get_sort()
                )

                solver.fts.assign_next(input_coreir_d0, input_coreir)
                solver.fts.assign_next(input_coreir_d1, input_coreir_d0)

                solver.fts.add_invar(
                    solver.create_term(
                        solver.ops.Equal, input_coreir_d1, input_pnr_short
                    )
                )

    for k, v in input_symbols_coreir.items():
        state_var = solver.create_fts_state_var(k + "_state", v.get_sort())
        input_var = solver.create_fts_input_var(k + "_input", v.get_sort())

        clk_low = solver.create_term(
            solver.ops.Equal,
            solver.clks[0],
            solver.create_term(0, solver.create_bvsort(1)),
        )

        solver.fts.assign_next(
            state_var,
            solver.create_term(solver.ops.Ite, clk_low, input_var, state_var),
        )

        solver.fts.add_invar(solver.create_term(solver.ops.Equal, state_var, v))


def get_output_array_idx(
    solver, bvsort16, mapped_output_var_name, valid_name, pnr=False
):
    pixel_index_var = solver.create_fts_state_var(
        f"pixel_index_{str(mapped_output_var_name)}", bvsort16
    )

    # Precalculate the halide pixel index based on the memory tile schedule
    assert valid_name in solver.stencil_valid_to_port_controller, breakpoint()
    memtile = solver.stencil_valid_to_port_controller[valid_name]

    # This is a list that stores the number of valid pixels at each cycle
    # Can use this to index into halide output pixel array
    cycle_to_idx, valids = mem_tile_get_num_valids(
        solver.stencil_valid_to_schedule[memtile],
        solver.max_cycles,
        iterator_support=6,
    )

    # PnR has an output IO tile register
    if pnr:
        cycle_to_idx = [0] + cycle_to_idx

    cycle_to_idx_var_lut = []

    for i, idx in enumerate(cycle_to_idx):
        cycle_to_idx_var_lut.append(
            (solver.create_term(i, bvsort16), solver.create_term(idx, bvsort16))
        )

    cycle_to_idx_var = solver.create_lut(
        f"{memtile}_cycle_to_idx_var",
        cycle_to_idx_var_lut,
        bvsort16,
        solver.create_bvsort(1),
    )

    pixel_index = cycle_to_idx_var(solver.cycle_count)

    solver.fts.add_invar(
        solver.create_term(solver.ops.Equal, pixel_index, pixel_index_var)
    )

    return pixel_index


def constrain_array_init(solver, array_var):
    idx_sort = array_var.get_sort().get_indexsort()
    elem_sort = array_var.get_sort().get_elemsort()
    empty_array = solver.create_term(
        solver.create_term(0, elem_sort), array_var.get_sort()
    )

    solver.fts.constrain_init(
        solver.create_term(solver.ops.Equal, array_var, empty_array)
    )


def compare_output_arrays(
    solver, coreir_output_array, pnr_output_array, coreir_valid_array, pnr_valid_array
):
    # Create property term that says valid is always 1
    property_term = solver.create_term(True)

    for cycle in range(solver.max_cycles):
        coreir_output = solver.create_term(
            solver.ops.Select,
            coreir_output_array,
            solver.create_const(cycle, solver.create_bvsort(16)),
        )
        pnr_output = solver.create_term(
            solver.ops.Select,
            pnr_output_array,
            solver.create_const(cycle, solver.create_bvsort(16)),
        )

        coreir_valid = solver.create_term(
            solver.ops.Select,
            coreir_valid_array,
            solver.create_const(cycle, solver.create_bvsort(16)),
        )
        pnr_valid = solver.create_term(
            solver.ops.Select,
            pnr_valid_array,
            solver.create_const(cycle, solver.create_bvsort(16)),
        )

        # prop = solver.create_term(
        #     solver.ops.Implies,
        #     solver.create_term(solver.ops.Equal, coreir_valid, solver.create_term(1, solver.create_bvsort(1))),
        #     solver.create_term(solver.ops.Equal, coreir_valid, pnr_valid),
        # )

        # property_term = solver.create_term(solver.ops.And, property_term, prop)

        both_valid = solver.create_term(
            solver.ops.And,
            solver.create_term(
                solver.ops.Equal,
                coreir_valid,
                solver.create_term(1, solver.create_bvsort(1)),
            ),
            solver.create_term(
                solver.ops.Equal,
                pnr_valid,
                solver.create_term(1, solver.create_bvsort(1)),
            ),
        )

        prop = solver.create_term(
            solver.ops.Implies,
            both_valid,
            solver.create_term(solver.ops.Equal, coreir_output, pnr_output),
        )

        property_term = solver.create_term(solver.ops.And, property_term, prop)

    return property_term


def create_pnr_property_term(
    solver,
    symbols_coreir,
    symbols_pnr,
    bvsort16,
    bvsort1,
    id_to_name,
    input_to_output_cycle_dep,
):

    coreir_to_pnr = {}
    coreir_to_pnr_valids = {}
    coreir_to_valid = {}
    pnr_to_valid = {}
    symbol_to_name = {}
    pnr_symbol_to_name = {}
    valid_symbols = []

    for pnr_symbol_name, pnr_symbol in symbols_pnr.items():
        pnr_id = pnr_symbol_name.split(".")[-1]
        pnr_coreir_name = id_to_name[pnr_id]

        for coreir_symbol_name, coreir_symbol in symbols_coreir.items():
            coreir_name = coreir_symbol_name.split(".")[-1]
            if coreir_name in pnr_coreir_name:

                if (
                    coreir_symbol.get_sort().get_width() == 1
                    and pnr_symbol.get_sort().get_width() == 1
                ):
                    coreir_to_pnr_valids[coreir_symbol] = pnr_symbol
                    symbol_to_name[coreir_symbol] = coreir_symbol_name
                    symbol_to_name[pnr_symbol] = pnr_coreir_name
                    valid_symbols.append(coreir_symbol)
                    valid_symbols.append(pnr_symbol)
                    pnr_symbol_to_name[pnr_symbol] = pnr_symbol_name
                else:
                    pnr_symbol_short = solver.fts.make_term(
                        ss.Op(
                            ss.primops.Extract,
                            coreir_symbol.get_sort().get_width() - 1,
                            0,
                        ),
                        pnr_symbol,
                    )
                    coreir_to_pnr[coreir_symbol] = pnr_symbol_short
                    symbol_to_name[coreir_symbol] = coreir_symbol_name
                    symbol_to_name[pnr_symbol_short] = pnr_coreir_name
                    pnr_symbol_to_name[pnr_symbol_short] = pnr_symbol_name

    name_to_symbol = {v: k for k, v in symbol_to_name.items()}

    for coreir_symbol, pnr_symbol in coreir_to_pnr.items():
        coreir_name = symbol_to_name[coreir_symbol]
        pnr_name = symbol_to_name[pnr_symbol]

        coreir_valid_name = f'{coreir_name.split("_write")[0]}_write_valid'
        assert coreir_valid_name in name_to_symbol

        coreir_valid = name_to_symbol[coreir_valid_name]

        coreir_to_valid[coreir_symbol] = coreir_valid

        pnr_to_valid[pnr_symbol] = coreir_to_pnr_valids[coreir_valid]

    # If solver.bmc_counter is less than to solver.first_valid_output
    output_dep_on_input = solver.create_term(
        solver.ops.BVUle,
        solver.bmc_counter,
        solver.create_term(2 * input_to_output_cycle_dep, bvsort16),
    )

    property_term = solver.create_term(True)

    # create an array and counter for each output variable
    for coreir_symbol, pnr_symbol in coreir_to_pnr.items():

        coreir_valid = coreir_to_valid[coreir_symbol]

        # create array for CoreIR output/valids
        coreir_output_array = solver.create_fts_state_var(
            symbol_to_name[coreir_symbol] + "_array",
            solver.solver.make_sort(
                ss.sortkinds.ARRAY, bvsort16, coreir_symbol.get_sort()
            ),
        )
        constrain_array_init(solver, coreir_output_array)
        coreir_valid_array = solver.create_fts_state_var(
            symbol_to_name[coreir_valid] + "_valid_array",
            solver.solver.make_sort(ss.sortkinds.ARRAY, bvsort16, bvsort1),
        )
        constrain_array_init(solver, coreir_valid_array)

        coreir_array_idx = get_output_array_idx(
            solver,
            bvsort16,
            symbol_to_name[coreir_symbol],
            symbol_to_name[coreir_valid],
        )

        # Store coreir_symbol in coreir_output_array at coreir_array_idx
        coreir_output_array_next = solver.create_term(
            solver.ops.Store,
            coreir_output_array,
            coreir_array_idx,
            coreir_symbol,
        )

        coreir_valid_array_next = solver.create_term(
            solver.ops.Store,
            coreir_valid_array,
            coreir_array_idx,
            coreir_valid,
        )

        pnr_valid = pnr_to_valid[pnr_symbol]

        # create array for pnr output/valids
        pnr_output_array = solver.create_fts_state_var(
            pnr_symbol_to_name[pnr_symbol] + "_array",
            solver.solver.make_sort(
                ss.sortkinds.ARRAY, bvsort16, pnr_symbol.get_sort()
            ),
        )
        constrain_array_init(solver, pnr_output_array)
        pnr_valid_array = solver.create_fts_state_var(
            pnr_symbol_to_name[pnr_valid] + "_valid_array",
            solver.solver.make_sort(ss.sortkinds.ARRAY, bvsort16, bvsort1),
        )
        constrain_array_init(solver, pnr_valid_array)

        pnr_array_idx = get_output_array_idx(
            solver,
            bvsort16,
            pnr_symbol_to_name[pnr_symbol],
            pnr_symbol_to_name[pnr_valid],
            pnr=True,
        )

        # Store pnr_symbol in pnr_output_array at pnr_array_idx
        pnr_output_array_next = solver.create_term(
            solver.ops.Store,
            pnr_output_array,
            pnr_array_idx,
            pnr_symbol,
        )

        pnr_valid_array_next = solver.create_term(
            solver.ops.Store,
            pnr_valid_array,
            pnr_array_idx,
            pnr_valid,
        )

        solver.fts.assign_next(
            coreir_output_array,
            solver.create_term(
                solver.ops.Ite,
                output_dep_on_input,
                coreir_output_array,
                coreir_output_array_next,
            ),
        )
        solver.fts.assign_next(
            coreir_valid_array,
            solver.create_term(
                solver.ops.Ite,
                output_dep_on_input,
                coreir_valid_array,
                coreir_valid_array_next,
            ),
        )
        solver.fts.assign_next(
            pnr_output_array,
            solver.create_term(
                solver.ops.Ite,
                output_dep_on_input,
                pnr_output_array,
                pnr_output_array_next,
            ),
        )
        solver.fts.assign_next(
            pnr_valid_array,
            solver.create_term(
                solver.ops.Ite,
                output_dep_on_input,
                pnr_valid_array,
                pnr_valid_array_next,
            ),
        )

        prop = compare_output_arrays(
            solver,
            coreir_output_array,
            pnr_output_array,
            coreir_valid_array,
            pnr_valid_array,
        )

        property_term = solver.create_term(solver.ops.And, property_term, prop)

    property_term = solver.create_term(
        solver.ops.Or, output_dep_on_input, property_term
    )

    return property_term, valid_symbols


def dump_comparison_array_contents(solver, bmc, coreir_symbols, pnr_symbols):

    witnesses = bmc.witness()
    for symbol_name in coreir_symbols + pnr_symbols:
        for var, val in witnesses[-1].items():
            if (
                symbol_name in str(var)
                and "_array" in str(var)
                and "next" not in str(var)
            ):
                print(var, val)
                t = re.findall("(bv\d*\s)\d*", str(val))
                if len(t) == 0:
                    t = re.findall("(#b\d*)", str(val))
                values = t[2::2]
                indices = t[1::2]
                print(tabulate(zip(indices, values), headers=["Index", "Value"]))
                print("\n")


def verify_pnr(interconnect, coreir_file, instance_to_instr, pipeline_config_interval):
    file_info = {}
    file_info["port_remapping"] = coreir_file.replace(
        "design_top_map.json", "design.port_remap"
    )
    app_dir = os.path.dirname(coreir_file)  # coreir_file has mapped dataflow graph

    cmod = read_coreir(coreir_file)
    nx = coreir_to_nx(cmod)

    interconnect.pipeline_config_interval = pipeline_config_interval

    solver = Solver()
    # solver.solver.set_opt("produce-models", "true")
    solver.file_info = file_info
    solver.app_dir = f"{app_dir}/verification"

    solver.max_cycles = 400

    solver, input_symbols_coreir, output_symbols_coreir = nx_to_smt(
        nx, interconnect, solver, app_dir
    )

    # load PnR results
    packed_file = coreir_file.replace("design_top_map.json", "design.packed")
    placement_file = coreir_file.replace("design_top_map.json", "design.place")
    routing_file = coreir_file.replace("design_top_map.json", "design.route")

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
        read_coreir(coreir_file.replace("design_top_map.json", "design_top.json")),
        instance_to_instr,
    )

    # nx_to_pdf(nx_pnr, f"{app_dir}/verification/pnr_graph.pdf")

    solver, input_symbols_pnr, output_symbols_pnr = nx_to_smt(
        nx_pnr, interconnect, solver, app_dir
    )

    set_clk_rst_flush(solver)
    synchronize_cycle_counts(solver)

    bvsort16 = solver.create_bvsort(16)
    bvsort1 = solver.create_bvsort(1)

    set_pnr_inputs(
        solver, input_symbols_coreir, input_symbols_pnr, bvsort16, id_to_name
    )

    input_to_output_cycle_dep = solver.first_valid_output

    property_term, valid_symbols = create_pnr_property_term(
        solver,
        output_symbols_coreir,
        output_symbols_pnr,
        bvsort16,
        bvsort1,
        id_to_name,
        input_to_output_cycle_dep,
    )

    print("Named terms", len(solver.fts.named_terms))
    print("State vars", len(solver.fts.statevars))
    print("Trans size", len(str(solver.fts.trans)))

    # property_term = solver.create_term(
    #    solver.ops.BVUlt, solver.bmc_counter, solver.create_term((solver.max_cycles * 2)-1, bvsort16)
    # )

    prop = pono.Property(solver.solver, property_term)

    bmc = pono.Bmc(prop, solver.fts, solver.solver)

    # check_pixels = 1
    # check_cycles = solver.first_valid_output + 1 + check_pixels
    check_cycles = solver.max_cycles
    print("First valid output at cycle", solver.first_valid_output)
    print("Running BMC for", check_cycles, "cycles")
    start = time.time()
    res = bmc.check_until(check_cycles * 2)
    print(time.time() - start)
    if res is None or res:

        # Create property term that says valid is always 0
        property_term = solver.create_term(True)
        for mapped_output_var in valid_symbols:

            valid_eq = solver.create_term(
                solver.ops.Equal, mapped_output_var, solver.create_term(0, bvsort1)
            )

            property_term = solver.create_term(solver.ops.And, property_term, valid_eq)

        prop = pono.Property(solver.solver, property_term)
        btor_solver = Solver(solver_name="btor")
        bmc = pono.Bmc(prop, solver.fts, btor_solver.solver)

        print("Checking that valid is high at least once for", check_cycles, "cycles")
        start = time.time()
        res2 = bmc.check_until(check_cycles * 2)
        print(time.time() - start)

        if res2 is None or res2:
            print("\n\033[91m" + "Valid is never high" + "\033[0m")
        else:
            print(
                "\n\033[92m" + "Formal check of mapped application passed" + "\033[0m"
            )

    else:

        # vcd_printer = pono.VCDWitnessPrinter(solver.fts, bmc.witness())
        # vcd_printer.dump_trace_to_file("/aha/dense_only_sparse.vcd")

        symbols = (
            list(output_symbols_coreir.keys())
            + list(output_symbols_pnr.keys())
            + list(input_symbols_pnr.keys())
            + list(input_symbols_coreir.keys())
        )

        waveform_signals = [
            "pixel_index_",
            "cycle_count",
            "halide_out",
        ]

        print_trace(solver, bmc, symbols, waveform_signals)

        dump_comparison_array_contents(
            solver,
            bmc,
            list(output_symbols_coreir.keys()),
            list(output_symbols_pnr.keys()),
        )

    # breakpoint()
