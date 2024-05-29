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
import math
import multiprocessing


def set_pnr_inputs(solver, input_symbols_pnr, input_symbols_pipelined, bvsort16):

    for k, v in input_symbols_pnr.items():
        pnr_name = k.split(".")[0]
        pipelined_var = pnr_name[0] + str(int(pnr_name[1:]) + 1000) + ".out"
        solver.fts.add_invar(
            solver.create_term(
                solver.ops.Equal, input_symbols_pipelined[pipelined_var], v
            )
        )

    for k, v in input_symbols_pnr.items():
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
        solver.starting_cycle,
        solver.max_cycles,
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
    # pass


def compare_output_arrays(
    solver, coreir_output_array, pnr_output_array, coreir_valid_array, pnr_valid_array
):
    # Create property term that says valid is always 1
    property_term = solver.create_term(True)

    for cycle in range(solver.starting_cycle, solver.max_cycles):
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
    symbols_pnr,
    symbols_pipelined,
    bvsort16,
    bvsort1,
    id_to_name_pnr,
    id_to_name_pipelined,
    input_to_output_cycle_dep,
):

    pnr_to_pipelined = {}
    pnr_to_valid = {}
    pipelined_to_valid = {}
    symbol_to_name = {}
    valid_symbols = []

    id_to_name_pnr_reversed = {v: k for k, v in id_to_name_pnr.items()}
    id_to_name_pipelined_reversed = {v: k for k, v in id_to_name_pipelined.items()}

    for k, v in symbols_pnr.items():
        if "I" in k:
            pnr_id = k.split(".")[-1]
            pnr_name = id_to_name_pnr[pnr_id]

            pipelined_id = id_to_name_pipelined_reversed[pnr_name]

            pnr_to_pipelined[v] = symbols_pipelined["out." + pipelined_id]

            pnr_valid_name = f'{pnr_name.split("_write")[0]}_write_valid'.replace(
                "io16", "io1"
            ).replace("io17", "io1")

            pnr_valid_id = id_to_name_pnr_reversed[pnr_valid_name]
            pipelined_valid_id = id_to_name_pipelined_reversed[pnr_valid_name]

            pnr_to_valid[v] = symbols_pnr["out." + pnr_valid_id]
            pipelined_to_valid[symbols_pipelined["out." + pipelined_id]] = (
                symbols_pipelined["out." + pipelined_valid_id]
            )

            symbol_to_name[v] = "out." + pnr_id
            symbol_to_name[symbols_pipelined["out." + pipelined_id]] = (
                "out." + pipelined_id
            )
            symbol_to_name[symbols_pnr["out." + pnr_valid_id]] = "out." + pnr_valid_id
            symbol_to_name[symbols_pipelined["out." + pipelined_valid_id]] = (
                "out." + pipelined_valid_id
            )

            valid_symbols.append(symbols_pnr["out." + pnr_valid_id])
            valid_symbols.append(symbols_pipelined["out." + pipelined_valid_id])

    # If solver.bmc_counter is less than to solver.first_valid_output
    output_dep_on_input = solver.create_term(
        solver.ops.BVUle,
        solver.bmc_counter,
        solver.create_term(2 * input_to_output_cycle_dep, bvsort16),
    )

    property_term = solver.create_term(True)

    # create an array and counter for each output variable
    for pnr_symbol, pipelined_symbol in pnr_to_pipelined.items():

        pipelined_valid = pipelined_to_valid[pipelined_symbol]

        # create array for CoreIR output/valids
        pipelined_output_array = solver.create_fts_state_var(
            symbol_to_name[pipelined_symbol] + "_array",
            solver.solver.make_sort(
                ss.sortkinds.ARRAY, bvsort16, pipelined_symbol.get_sort()
            ),
        )
        constrain_array_init(solver, pipelined_output_array)
        pipelined_valid_array = solver.create_fts_state_var(
            symbol_to_name[pipelined_valid] + "_valid_array",
            solver.solver.make_sort(ss.sortkinds.ARRAY, bvsort16, bvsort1),
        )
        constrain_array_init(solver, pipelined_valid_array)

        pipelined_array_idx = get_output_array_idx(
            solver,
            bvsort16,
            symbol_to_name[pipelined_symbol],
            symbol_to_name[pipelined_valid],
            pnr=True,
        )

        # Store pipelined_symbol in pipelined_output_array at pipelined_array_idx
        pipelined_output_array_next = solver.create_term(
            solver.ops.Store,
            pipelined_output_array,
            pipelined_array_idx,
            pipelined_symbol,
        )

        pipelined_valid_array_next = solver.create_term(
            solver.ops.Store,
            pipelined_valid_array,
            pipelined_array_idx,
            pipelined_valid,
        )

        pnr_valid = pnr_to_valid[pnr_symbol]

        # create array for pnr output/valids
        pnr_output_array = solver.create_fts_state_var(
            symbol_to_name[pnr_symbol] + "_array",
            solver.solver.make_sort(
                ss.sortkinds.ARRAY, bvsort16, pnr_symbol.get_sort()
            ),
        )
        constrain_array_init(solver, pnr_output_array)
        pnr_valid_array = solver.create_fts_state_var(
            symbol_to_name[pnr_valid] + "_valid_array",
            solver.solver.make_sort(ss.sortkinds.ARRAY, bvsort16, bvsort1),
        )
        constrain_array_init(solver, pnr_valid_array)

        pnr_array_idx = get_output_array_idx(
            solver,
            bvsort16,
            symbol_to_name[pnr_symbol],
            symbol_to_name[pnr_valid],
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
            pipelined_output_array,
            solver.create_term(
                solver.ops.Ite,
                output_dep_on_input,
                pipelined_output_array,
                pipelined_output_array_next,
            ),
        )
        solver.fts.assign_next(
            pipelined_valid_array,
            solver.create_term(
                solver.ops.Ite,
                output_dep_on_input,
                pipelined_valid_array,
                pipelined_valid_array_next,
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
            pipelined_output_array,
            pnr_output_array,
            pipelined_valid_array,
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


def verify_pipeline_parallel(
    interconnect,
    coreir_file,
    instance_to_instr,
    instance_to_instr_pipelined,
    pipeline_config_interval,
    starting_cycle,
    ending_cycle,
):
    file_info = {}
    file_info["port_remapping"] = coreir_file.replace(
        "design_top.json", "design.port_remap"
    )
    app_dir = os.path.dirname(coreir_file)  # coreir_file has mapped dataflow graph

    interconnect.pipeline_config_interval = pipeline_config_interval

    solver = Solver()
    # solver.solver.set_opt("produce-models", "true")
    solver.file_info = file_info
    # solver.app_dir = f"{app_dir}/verification"
    solver.app_dir = f"{app_dir}/verification_{starting_cycle}"

    solver.starting_cycle = starting_cycle
    solver.max_cycles = ending_cycle

    # load PnR results
    packed_file = coreir_file.replace("design_top.json", "design_pnr.packed")
    placement_file = coreir_file.replace("design_top.json", "design_pnr.place")
    routing_file = coreir_file.replace("design_top.json", "design_pnr.route")

    netlist, buses = pythunder.io.load_netlist(packed_file)
    id_to_name_pnr = pythunder.io.load_id_to_name(packed_file)

    solver.id_to_name = id_to_name_pnr

    placement = load_placement(placement_file)
    routing = load_routing_result(routing_file)

    # Construct PnR result graph
    routing_result_graph_pnr = construct_graph(
        placement, routing, id_to_name_pnr, netlist, 1, 0, 1, False
    )

    nx_pnr = pnr_to_nx(
        routing_result_graph_pnr,
        read_coreir(coreir_file.replace("design_top.json", "design_top_pnr.json")),
        instance_to_instr,
    )

    solver, input_symbols_pnr, output_symbols_pnr = nx_to_smt(
        nx_pnr, interconnect, solver
    )

    # Pipelined PnR graph

    # load PnR results
    packed_file = coreir_file.replace("design_top.json", "design.packed")
    placement_file = coreir_file.replace("design_top.json", "design.place")
    routing_file = coreir_file.replace("design_top.json", "design.route")

    netlist, buses = pythunder.io.load_netlist(packed_file)
    id_to_name_pipelined = pythunder.io.load_id_to_name(packed_file)

    solver.id_to_name = id_to_name_pipelined

    placement = load_placement(placement_file)
    routing = load_routing_result(routing_file)

    # Construct PnR result graph
    routing_result_graph = construct_graph(
        placement, routing, id_to_name_pipelined, netlist, 1, 0, 1, False
    )

    nx_pipelined = pnr_to_nx(
        routing_result_graph,
        read_coreir(coreir_file.replace("design_top.json", "design_top.json")),
        instance_to_instr,
    )

    solver, input_symbols_pipelined, output_symbols_pipelined = nx_to_smt(
        nx_pipelined, interconnect, solver
    )

    # nx_to_pdf(nx_pnr, f"{app_dir}/verification/pnr_graph")
    # nx_to_pdf(nx_pipelined, f"{app_dir}/verification/pipelined_graph")

    set_clk_rst_flush(solver)
    synchronize_cycle_counts(solver)

    bvsort16 = solver.create_bvsort(16)
    bvsort1 = solver.create_bvsort(1)

    set_pnr_inputs(solver, input_symbols_pnr, input_symbols_pipelined, bvsort16)

    input_to_output_cycle_dep = solver.first_valid_output

    property_term, valid_symbols = create_pnr_property_term(
        solver,
        output_symbols_pnr,
        output_symbols_pipelined,
        bvsort16,
        bvsort1,
        id_to_name_pnr,
        id_to_name_pipelined,
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
    check_cycles = solver.max_cycles - solver.starting_cycle
    print("First valid output at cycle", solver.first_valid_output)
    print("Running BMC for", check_cycles, "cycles")
    start = time.time()
    res = bmc.check_until(check_cycles * 2)
    print(time.time() - start)
    if res is None or res:

        # Create property term that says valid is always 0
        # property_term = solver.create_term(True)
        # for mapped_output_var in valid_symbols:

        #     valid_eq = solver.create_term(
        #         solver.ops.Equal, mapped_output_var, solver.create_term(0, bvsort1)
        #     )

        #     property_term = solver.create_term(solver.ops.And, property_term, valid_eq)

        # prop = pono.Property(solver.solver, property_term)
        # btor_solver = Solver(solver_name="btor")
        # bmc = pono.Bmc(prop, solver.fts, btor_solver.solver)

        # print("Checking that valid is high at least once for", check_cycles, "cycles")
        # start = time.time()
        # res2 = bmc.check_until(check_cycles * 2)
        # print(time.time() - start)

        # if res2 is None or res2:
        #     print("\n\033[91m" + "Valid is never high" + "\033[0m")
        # else:
        #     print(
        #         "\n\033[92m" + "Formal check of mapped application passed" + "\033[0m"
        #     )

        print(
            "\n\033[92m" + "Formal check of mapped application passed" + "\033[0m",
            starting_cycle,
        )
    else:

        # vcd_printer = pono.VCDWitnessPrinter(solver.fts, bmc.witness())
        # vcd_printer.dump_trace_to_file("/aha/dense_only_sparse.vcd")

        symbols = (
            list(output_symbols_pipelined.keys())
            + list(output_symbols_pnr.keys())
            + list(input_symbols_pnr.keys())
            + list(input_symbols_pipelined.keys())
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
            list(output_symbols_pipelined.keys()),
            list(output_symbols_pnr.keys()),
        )
        raise Exception("Counterexample found")
    # breakpoint()


import concurrent.futures


def get_first_output_from_coreir(coreir_file):

    app_name = coreir_file.split("/")[-3]

    with open(coreir_file, "r") as f:
        lines = f.readlines()

        for line in lines:
            if 'in2glb_0"' in line:
                return int(line.split('cycle_starting_addr":[')[-1].split("]")[0])


def verify_pipeline(
    interconnect,
    coreir_file,
    instance_to_instr,
    instance_to_instr_pipelined,
    pipeline_config_interval,
):

    first_output_pixel_at_cycle = get_first_output_from_coreir(coreir_file)

    total_output_pixels = 64 * 64
    num_cores = 32

    total_cycles = total_output_pixels + first_output_pixel_at_cycle

    pixels_per_core = math.ceil(total_output_pixels / num_cores)

    check_pixels = []

    check_pixel = 0
    while check_pixel < total_output_pixels:
        starting_cycle = check_pixel
        ending_cycle = (
            starting_cycle + pixels_per_core + first_output_pixel_at_cycle - 1
        )
        # verify_pipeline_parallel(interconnect, coreir_file, starting_cycle, ending_cycle)
        # print("Checking pixels", starting_cycle, "to", ending_cycle)
        check_pixels.append((starting_cycle, ending_cycle))
        check_pixel += pixels_per_core

    def verify_pipeline_parallel_wrapper(args):
        starting_cycle, ending_cycle = args
        print("Checking pixels", starting_cycle, "to", ending_cycle)
        verify_pipeline_parallel(
            interconnect,
            coreir_file,
            instance_to_instr,
            instance_to_instr_pipelined,
            pipeline_config_interval,
            starting_cycle,
            ending_cycle,
        )

    if False:
        results = []
        processes = []
        for check_pixel in check_pixels:
            process = multiprocessing.Process(
                target=verify_pipeline_parallel_wrapper, args=(check_pixel,)
            )
            processes.append(process)
            process.start()

        for process in processes:
            process.join()
            results.append(process.exitcode)

        if 1 in results:
            print("\n\033[91m" + "Failed" + "\033[0m")
        else:
            print("\n\033[92m" + "Passed" + "\033[0m")
    else:

        verify_pipeline_parallel_wrapper((0, 200))

    # breakpoint()
