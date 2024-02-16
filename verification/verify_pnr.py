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
from .verify_design_top import import_from, print_trace, flatten, set_clk_rst_flush

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
                

    for k,v in input_symbols_coreir.items():
        state_var = solver.create_fts_state_var(k + "_state", v.get_sort())
        input_var = solver.create_fts_input_var(k + "_input", v.get_sort())

        clk_low = solver.create_term(
            solver.ops.Equal, solver.clks[0], solver.create_term(0, solver.create_bvsort(1))
        )

        solver.fts.assign_next(
            state_var,
            solver.create_term(
                solver.ops.Ite, clk_low, input_var, state_var
            ),
        )

        solver.fts.add_invar(solver.create_term(solver.ops.Equal, state_var, v))


def compare_output_array(
    solver, bvsort16, index, array0, array1, max_index, pnr_valid, bvsort1
):
    # array0 = coreir outputs
    # array1 = pnr outputs
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
            solver.ops.BVUle, #BVUle
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
    # return solver.create_term( # Claim that pnr_valid is low
    #         solver.ops.Equal,
    #         pnr_valid, 
    #         solver.create_term(0, bvsort1)
    #     )

def create_property_term(
    solver, output_symbols_coreir, output_symbols_pnr, 
    bvsort16, bvsort1, id_to_name, num_output_pixels
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

    property_term = solver.create_term(
        solver.ops.Equal, solver.create_term(0, bvsort1), solver.create_term(0, bvsort1)
    )

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
        # ARE WE SURE ABOUT THIS????
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
        prop = compare_output_array(solver, bvsort16, min_out_pixel_count, 
                            coreir_output_array, pnr_output_array, num_output_pixels, pnr_valid, bvsort1)

        property_term = solver.create_term(
            solver.ops.And, property_term, prop
        )
        breakpoint()
    
    return property_term

 
def verify_pnr(interconnect, coreir_file):
    file_info = {}
    file_info["port_remapping"] = coreir_file.replace(
        "design_top.json", "design.port_remap"
    )
    app_dir = os.path.dirname(coreir_file) # coreir_file has mapped dataflow graph

    sys.path.append(os.path.abspath(app_dir))

    create_app = import_from(
        f"{app_dir.split(os.sep)[-2]}_pono_testbench", "create_app"
    )

    hw_input_stencil, hw_output_stencil = create_app(Solver())

    cmod  = read_coreir(coreir_file)
    nx = coreir_to_nx(cmod) # translate coreir to network x
    print("CoreIR to NX done.")
    coreir_to_pdf(nx,"/aha/nx_pdf/coreir_graph")

    # Instantiate solver object
    solver = Solver()
    solver.solver.set_opt("produce-models", "true")
    solver.file_info = file_info
    solver.app_dir = f"{app_dir}/verification"

    solver, input_symbols_coreir, output_symbols_coreir = nx_to_smt(
        nx, interconnect, solver, app_dir
    ) # network x to SMT

    print("NX to SMT done.")

    # load PnR results
    packed_file = coreir_file.replace("design_top.json", "design.packed")
    placement_file = coreir_file.replace("design_top.json", "design.place")
    routing_file = coreir_file.replace("design_top.json", "design.route")

    netlist, buses = pythunder.io.load_netlist(packed_file)
    id_to_name = pythunder.io.load_id_to_name(packed_file)

    placement = load_placement(placement_file)
    routing = load_routing_result(routing_file)
    print("PnR results loaded.")

    # Construct PnR result graph
    routing_result_graph = construct_graph(
        placement, routing, id_to_name, netlist, 1, 0, 1, False
    )
    print("PnR graph created.")

    nx_pnr = pnr_to_nx(routing_result_graph, cmod) # translate pnr graph to network x
    # add cmod as parameter
    print("PnR NX generated.")


    solver, input_symbols_pnr, output_symbols_pnr = nx_to_smt(
        nx_pnr, interconnect, solver, app_dir
    ) # network x to SMT for PnR

    set_clk_rst_flush(solver)

    bvsort16 = solver.create_bvsort(16)
    bvsort1 = solver.create_bvsort(1)

    set_inputs(solver, input_symbols_coreir, input_symbols_pnr, 
            bvsort16, id_to_name)
    
    
    property_term = create_property_term(
        solver, 
        output_symbols_coreir, 
        output_symbols_pnr, 
        bvsort16, 
        bvsort1, 
        id_to_name,
        len(flatten(hw_output_stencil))
    )
    print(len(flatten(hw_output_stencil)))

    prop = pono.Property(solver.solver, property_term) # create property

    bmc = pono.Bmc(prop, solver.fts, solver.solver) # run bmc checker

    print("Running BMC...")
    start = time.time()
    res = bmc.check_until(20)
    print("BMC time:", time.time() - start)

    if res is None or res:
        print("\n\033[92m" + "Formal check of mapped application passed" + "\033[0m")
    else:
        trace_symbols = list(output_symbols_coreir.keys()) + list(output_symbols_pnr.keys()) + list(input_symbols_pnr.keys()) + list(input_symbols_coreir.keys()) + \
                        ["out.hw_output_stencil_op_hcompute_hw_output_stencil_write_0_array","|((_ extract 15 0) I0.f2io_16)_array|","out_count_out.hw_output_stencil_op_hcompute_hw_output_stencil_write_0","out_count_I0.f2io_16"]
        print_trace(bmc, trace_symbols)

    breakpoint()
