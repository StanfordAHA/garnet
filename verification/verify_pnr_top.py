from verified_agile_hardware.coreir_utils import (
    read_coreir,
    coreir_to_nx,
    coreir_to_pdf,
    nx_to_smt,
    pnr_to_nx,
)
from memory_core.memtile_util import LakeCoreBase
import time
import os
import pono
from simple_colors import *
import re
from tabulate import tabulate

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
from archipelago.visualize import visualize_pnr
from verified_agile_hardware.solver import Solver, Rewriter
import smt_switch as ss


def create_conv_smt(conv_solver):
    image_width = 32
    image_height = 32

    kernel_width = 3
    kernel_height = 3

    bvsort16 = conv_solver.create_bvsort(16)

    # Create an SMT variable (symbol) for every input pixel
    in_image_symbols = []
    for y in range(image_height):
        in_image_symbols.append([])
        for x in range(image_width):
            init_sym = conv_solver.create_fts_state_var(
                f"init_in_image_{x}_{y}", bvsort16
            )
            input_sym = conv_solver.create_fts_state_var(f"in_image_{x}_{y}", bvsort16)
            in_image_symbols[y].append(input_sym)
            conv_solver.fts.constrain_init(
                conv_solver.create_term(conv_solver.ops.Equal, input_sym, init_sym)
            )
            conv_solver.fts.assign_next(input_sym, input_sym)

    # Create SMT variable for every kernel value
    kernel_symbols = []
    for y in range(kernel_height):
        kernel_symbols.append([])
        for x in range(kernel_width):
            init_sym = conv_solver.create_fts_state_var(
                f"init_kernel_{x}_{y}", bvsort16
            )
            kernel_sym = conv_solver.create_fts_state_var(f"kernel_{x}_{y}", bvsort16)
            kernel_symbols[y].append(kernel_sym)
            conv_solver.fts.constrain_init(
                conv_solver.create_term(conv_solver.ops.Equal, kernel_sym, init_sym)
            )
            conv_solver.fts.assign_next(kernel_sym, kernel_sym)

    # Create array of output equations
    # out_symbols[y][x] is the equation representing the output pixel value at that point
    out_symbols = []
    for i_y in range(image_height):
        out_symbols.append([])
        for i_x in range(image_width):
            accum = []
            for k_y in range(kernel_height):
                for k_x in range(kernel_width):
                    if i_y + kernel_height <= len(
                        in_image_symbols
                    ) and i_x + kernel_width <= len(in_image_symbols[i_y + k_y]):
                        accum.append(
                            conv_solver.create_term(
                                conv_solver.ops.BVMul,
                                in_image_symbols[i_y + k_y][i_x + k_x],
                                kernel_symbols[k_y][k_x],
                            )
                        )

            if len(accum) > 1:
                out_symbols[i_y].append(
                    conv_solver.create_term(conv_solver.ops.BVAdd, *accum)
                )

    return in_image_symbols, kernel_symbols, out_symbols


def set_clk_rst_flush(solver):
    for clk in solver.clks:
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
    for rst in solver.rsts:
        if rst in solver.fts.inputvars:
            solver.fts.promote_inputvar(rst)
        solver.fts.constrain_init(
            solver.create_term(
                solver.ops.Equal, rst, solver.create_term(0, rst.get_sort())
            )
        )
        solver.fts_assert_at_times(
            rst,
            solver.create_term(0, rst.get_sort()),
            solver.create_term(1, rst.get_sort()),
            rst_times,
        )

    flush_times = [2, 3]
    for flush in solver.flushes:
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


def set_inputs(solver, input_symbols_coreir, input_symbols_pnr, 
            bvsort16, id_to_name):
    # Map pnr symbols to names
    input_pnr_symbols_to_names = {}
    for input_symbol_pnr in input_symbols_pnr:
        input_pnr_id = input_symbol_pnr.split(".")[0]
        input_pnr_name = id_to_name[input_pnr_id]
        input_pnr_symbols_to_names[input_symbol_pnr] = input_pnr_name
    
    # reverse map for pnr names to symbols
    input_pnr_symbols_to_names_reversed = {v: k for k, v in input_pnr_symbols_to_names.items()}
    
    # set each input symbol in coreir and pnr graphs equal
    for input_coreir_name in input_symbols_coreir:
        # find the matching pnr input
        input_coreir_name_sliced = input_coreir_name.split(".")[1]
        for input_pnr_name in input_pnr_symbols_to_names_reversed:
            if (input_coreir_name_sliced in input_pnr_name):
                # map pnr input name back to key symbol
                input_pnr_symbol = input_pnr_symbols_to_names_reversed[input_pnr_name]
                # map coreir name and pnr ID back to nodes
                input_coreir = input_symbols_coreir[input_coreir_name]
                input_pnr = input_symbols_pnr[input_pnr_symbol]
                input_pnr_short = solver.fts.make_term(
                    ss.Op(ss.primops.Extract, input_coreir.get_sort().get_width() - 1, 0),
                    input_pnr,
                )
                
                solver.fts.add_invar(solver.create_term(solver.ops.Equal, input_coreir, input_pnr_short))
                


def compare_output_array(
    solver, bvsort16, index, array0, array1, max_index
):
    # Create term initialize to true
    term = solver.create_term(
        solver.ops.Equal,
        solver.create_term(0, bvsort16),
        solver.create_term(0, bvsort16),
    )
    # Compare each element from 2 arrays up to index
    for idx in range(max_index):
        idx_bv = solver.create_term(idx, bvsort16)
        t = solver.create_term(
            solver.ops.Equal,
            solver.create_term(solver.ops.Select, array0, idx_bv),
            solver.create_term(solver.ops.Select, array1, idx_bv)
        )
        ############# DEBUG############
        t_n = solver.create_term(
            solver.ops.BVUgt,
            solver.create_term(solver.ops.Select, array0, idx_bv),
            solver.create_term(solver.ops.Select, array1, idx_bv)
        )
        ################################
        
        # check if idx is less than index
        idx_in_range = solver.create_term(solver.ops.BVUlt, 
                            idx_bv, 
                            index)
        # update term if idx < index
        # new_term = solver.create_term(solver.ops.And, term, t)
        # term = solver.create_term(
        #         solver.ops.Ite, 
        #         idx_in_range, 
        #         new_term, 
        #         term
        # )

        ################### DEBUG ####################
        new_term_n = solver.create_term(solver.ops.And, term, t_n)
        term = solver.create_term(
                solver.ops.Ite, 
                idx_in_range, 
                new_term_n, 
                term
        )
        ##########################################
    return term


def create_property_term(
    solver, output_symbols_coreir, output_symbols_pnr, 
    bvsort16, bvsort1, id_to_name
):
    # Pair up coreir outputs with pnr outputs
    # create separate lists for 16-bit and 1-bit outputs
    # Map pnr symbols to names
    output_pnr_symbols_to_names = {}
    for output_symbol_pnr in output_symbols_pnr:
        output_pnr_id = output_symbol_pnr.split(".")[0]
        output_pnr_name = id_to_name[output_pnr_id]
        output_pnr_symbols_to_names[output_symbol_pnr] = output_pnr_name
    
    # reverse map for pnr names to symbols
    output_pnr_symbols_to_names_reversed = {v: k for k, v in output_pnr_symbols_to_names.items()}

    # for each coreir output, find matching pnr output
    output_pair_1_bit = []
    output_pair_16_bit = []
    output_pair_1_bit_names = []
    output_pair_16_bit_names = []
    for output_coreir_name in output_symbols_coreir:
        # find the matching pnr output
        output_coreir_name_sliced = output_coreir_name.split(".")[1]
        for output_pnr_name in output_pnr_symbols_to_names_reversed:
            if (output_coreir_name_sliced in output_pnr_name):
                # map pnr output name back to key symbol
                output_pnr_symbol = output_pnr_symbols_to_names_reversed[output_pnr_name]
                # map coreir name and pnr ID back to nodes
                output_coreir = output_symbols_coreir[output_coreir_name]
                output_pnr = output_symbols_pnr[output_pnr_symbol]

                # find if the pair of outputs is 1 bit or 16 bit
                if (output_coreir.get_sort().get_width() == 1 and 
                    output_pnr.get_sort().get_width() == 1):
                    # if both 1 bits
                    output_pair_1_bit.append([output_coreir,output_pnr])
                    output_pair_1_bit_names.append([output_coreir_name,output_pnr_symbol])
                elif (output_coreir.get_sort().get_width() >= 16 and 
                      output_pnr.get_sort().get_width() >= 16):
                    # if both 16 bits
                    output_pnr_short = solver.fts.make_term(
                        ss.Op(ss.primops.Extract, output_coreir.get_sort().get_width() - 1, 0),
                        output_pnr,
                    )
                    output_pair_16_bit.append([output_coreir,output_pnr_short])
                    output_pair_16_bit_names.append([output_coreir_name,output_pnr_symbol])
                else:
                    print("OUTPUT FORMAT DID NOT MATCH!!!!")
                    breakpoint()

    
    # create an array and counter for each output variable
    for i in range(len(output_pair_16_bit_names)):
        # for each pair of CoreIR & PnR outputs, find the variables and var names
        output_pair_names = output_pair_16_bit_names[i]
        coreir_output_var_name = output_pair_names[0]
        pnr_output_var_name = output_pair_names[1]

        # coreir_output_var = output_symbols_coreir[coreir_output_var_name]
        # pnr_output_var = output_symbols_pnr[pnr_output_var_name]
        coreir_output_var = output_pair_16_bit[i][0]
        pnr_output_var = output_pair_16_bit[i][1]

        # clk_low variable; useful for counting valid outputs
        clk_low = solver.create_term(
            solver.ops.Equal, solver.clks[0], solver.create_term(0, bvsort1)
        )

        # create array for CoreIR output
        coreir_output_array_name = str(coreir_output_var)+"_array"
        coreir_output_array = solver.create_fts_state_var(coreir_output_array_name, 
                                solver.solver.make_sort(ss.sortkinds.ARRAY, 
                                bvsort16, bvsort16) # last 2 param = index_type, data_type, both 16 bit vec in this case
        )

        # find valid signal for coreir variable
        coreir_valid_name = f'{coreir_output_var_name.split("_write")[0]}_write_valid'
        assert coreir_valid_name in output_symbols_coreir
        coreir_valid = output_symbols_coreir[coreir_valid_name]

        # signal for checking if coreir_valid is high
        coreir_valid_eq = solver.create_term(
            solver.ops.Equal, coreir_valid, solver.create_term(1, bvsort1)
        ) 
        coreir_valid_and_clk_low = solver.create_term(solver.ops.And, coreir_valid_eq, clk_low)

        # create variable for counting valid coreir outputs
        coreir_out_pixel_count = solver.create_fts_state_var(
            f"out_count_{str(coreir_output_var_name)}", bvsort16
        )
        solver.fts.constrain_init(
            solver.create_term(
                solver.ops.Equal, coreir_out_pixel_count, solver.create_term(0, bvsort16)
            )
        ) # initialize count to 0
        coreir_count_plus_one = solver.create_term(
            solver.ops.BVAdd, coreir_out_pixel_count, solver.create_term(1, bvsort16)
        ) # variable for holding count+1

        # if valid and clk low, increment count
        solver.fts.assign_next(
            coreir_out_pixel_count,
            solver.create_term(
                solver.ops.Ite, 
                coreir_valid_and_clk_low, 
                coreir_count_plus_one, 
                coreir_out_pixel_count
            ),
        )

        # array updated with new output
        coreir_output_array_updated = solver.create_term(
            solver.ops.Store, 
            coreir_output_array, 
            coreir_out_pixel_count, # array index
            coreir_output_var # element data
        )

        # if valid and clk low, update array
        solver.fts.assign_next(
            coreir_output_array,
            solver.create_term(
                solver.ops.Ite, 
                coreir_valid_and_clk_low, 
                coreir_output_array_updated, 
                coreir_output_array
            ),
        )

        # create array for pnr output
        pnr_output_array_name = str(pnr_output_var)+"_array"
        pnr_output_array = solver.create_fts_state_var(pnr_output_array_name, 
                                solver.solver.make_sort(ss.sortkinds.ARRAY, 
                                bvsort16, bvsort16) # last 2 param = index_type, data_type, both 16 bit vec in this case
        )

        # find valid signal for pnr variable
        pnr_valid_name = f'{pnr_output_var_name.lower().split("_")[0]}_1'
        assert pnr_valid_name in output_symbols_pnr
        pnr_valid = output_symbols_pnr[pnr_valid_name]

        # signal for checking if pnr_valid is high
        pnr_valid_eq = solver.create_term(
            solver.ops.Equal, pnr_valid, solver.create_term(1, bvsort1)
        ) 
        pnr_valid_and_clk_low = solver.create_term(solver.ops.And, pnr_valid_eq, clk_low)

        # create variable for counting valid pnr outputs
        pnr_out_pixel_count = solver.create_fts_state_var(
            f"out_count_{str(pnr_output_var_name)}", bvsort16
        )
        solver.fts.constrain_init(
            solver.create_term(
                solver.ops.Equal, pnr_out_pixel_count, solver.create_term(0, bvsort16)
            )
        ) # initialize count to 0
        pnr_count_plus_one = solver.create_term(
            solver.ops.BVAdd, pnr_out_pixel_count, solver.create_term(1, bvsort16)
        ) # variable for holding count+1

        # if valid and clk low, increment count
        solver.fts.assign_next(
            pnr_out_pixel_count,
            solver.create_term(
                solver.ops.Ite, 
                pnr_valid_and_clk_low, 
                pnr_count_plus_one, 
                pnr_out_pixel_count
            ),
        )

        # array updated with new output
        pnr_output_array_updated = solver.create_term(
            solver.ops.Store, 
            pnr_output_array, 
            pnr_out_pixel_count, # array index
            pnr_output_var # element data
        )

        # if valid and clk low, update array
        solver.fts.assign_next(
            pnr_output_array,
            solver.create_term(
                solver.ops.Ite, 
                pnr_valid_and_clk_low, 
                pnr_output_array_updated, 
                pnr_output_array
            ),
        )

        # find minimum counter value of coreir and pnr valids
        coreir_less_count = solver.create_term(solver.ops.BVUlt, 
                            coreir_out_pixel_count, 
                            pnr_out_pixel_count)

        min_out_pixel_count = solver.create_term(
                solver.ops.Ite, 
                coreir_less_count, 
                coreir_out_pixel_count, 
                pnr_out_pixel_count)
        
        # return term
        property_term = compare_output_array(solver, bvsort16, min_out_pixel_count, 
                            coreir_output_array, pnr_output_array, 20)
        # remember to get actual max size
        return property_term



def print_trace(bmc, mapped_output_datas, mapped_output_valids):
    print("Counterexample found")

    trace_table = []

    trace = ["0step"]
    trace += list(range(len(bmc.witness())))
    trace_table.append(trace)

    trace = ["1clock"]
    t = list(range(len(bmc.witness())))
    trace += [int(n / 2) for n in t]
    trace_table.append(trace)

    waveform_signals = [
        "in.hw_input",
        "out_count_",
        "out_symbol_decoder_",
        "out_symbol_data_eq_",
        "in_symbol_",
    ]

    witnesses = bmc.witness()
    for var, _ in witnesses[0].items():
        display = False
        for signal in waveform_signals:
            if signal in str(var):
                display = True

        if str(var) in mapped_output_datas or str(var) in mapped_output_valids:
            display = True

        if "next" in str(var):
            display = False

        if display:
            trace = [str(var)]
            for witness in witnesses:
                val = witness[var]

                if "bv" in str(val):
                    val = re.split("bv(\d*)", str(val))[1].strip()

                if "false" in str(val):
                    trace.append(red("0"))
                elif "true" in str(val):
                    trace.append(green("1"))
                elif int(str(val)) == 0:
                    trace.append(red(str(val)))
                else:
                    trace.append(green(str(val)))

            trace_table.append(trace)
    trace_table.sort()
    print(tabulate(trace_table))


def load_id_to_name(id_filename):
    fin = open(id_filename, "r")
    lines = fin.readlines()
    id_to_name = {}


    for line in lines:
        id_to_name[line.split(": ")[0]] = line.split(": ")[1].rstrip()


    return id_to_name


def verify_pnr_top(interconnect, coreir_file):
    file_info = {}
    file_info["port_remapping"] = coreir_file.replace(
        "design_top.json", "design.port_remap"
    )
    app_dir = os.path.dirname(coreir_file) # coreir_file has mapped dataflow graph

    cmod  = read_coreir(coreir_file)
    nx = coreir_to_nx(cmod) # translate coreir to network x
    print("CoreIR to NX done.")
    coreir_to_pdf(nx,"/aha/nx_pdf/coreir_graph")

    # Instantiate solver object
    solver = Solver()
    solver.solver.set_opt("produce-models", "true")
    solver.file_info = file_info
    solver.app_dir = f"{app_dir}/verification"

    # solver, input_symbols, output_symbols = nx_to_smt(
    #     nx, interconnect, file_info, app_dir
    # ) # network x to SMT
    solver, input_symbols_coreir, output_symbols_coreir = nx_to_smt(
        nx, interconnect, solver, app_dir
    ) # network x to SMT

    print("NX to SMT done.")
    

    # load PnR results
    visualize = False
    sparse = False
    packed_file = coreir_file.replace("design_top.json", "design.packed")
    placement_file = coreir_file.replace("design_top.json", "design.place")
    routing_file = coreir_file.replace("design_top.json", "design.route")


    netlist, buses = pythunder.io.load_netlist(packed_file)

    
    id_to_name = pythunder.io.load_id_to_name(packed_file)
    # id_to_name_reversed = {v: k for k, v in id_to_name.items()}


    placement = load_placement(placement_file)
    routing = load_routing_result(routing_file)
    print("PnR results loaded.")


    if "PIPELINED" in os.environ and os.environ["PIPELINED"].isnumeric():
        pe_latency = int(os.environ["PIPELINED"])
    else:
        pe_latency = 1


    if "IO_DELAY" in os.environ and os.environ["IO_DELAY"] == "0":
        io_cycles = 0
    else:
        io_cycles = 1

    # Construct PnR result graph
    routing_result_graph = construct_graph(
        placement, routing, id_to_name, netlist, pe_latency, 0, io_cycles, sparse
    )
    print("PnR graph created.")

    nx_pnr = pnr_to_nx(routing_result_graph, cmod) # translate pnr graph to network x
    # add cmod as parameter
    print("PnR NX generated.")

    coreir_to_pdf(nx_pnr,"/aha/nx_pdf/pnr_graph2")


    solver, input_symbols_pnr, output_symbols_pnr = nx_to_smt(
        nx_pnr, interconnect, solver, app_dir
    ) # network x to SMT for PnR

    set_clk_rst_flush(solver)

    bvsort16 = solver.create_bvsort(16)
    bvsort1 = solver.create_bvsort(1)

    set_inputs(solver, input_symbols_coreir, input_symbols_pnr, 
            bvsort16, id_to_name)
    
    # breakpoint()
    property_term = create_property_term(
        solver, 
        output_symbols_coreir, 
        output_symbols_pnr, 
        bvsort16, 
        bvsort1, 
        id_to_name
    )


    prop = pono.Property(solver.solver, property_term) # create property

    print(prop.prop)

    bmc = pono.Bmc(prop, solver.fts, solver.solver) # run bmc checker

    print("Running BMC...")
    start = time.time()
    res = bmc.check_until(100)
    print("BMC time:", time.time() - start)

    if res is None or res:
        print("\n\033[92m" + "Formal check of mapped application passed" + "\033[0m")
    else:
        print_trace(bmc, mapped_output_datas, mapped_output_valids)

    breakpoint()
