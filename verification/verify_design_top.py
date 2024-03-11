from verified_agile_hardware.coreir_utils import (
    read_coreir,
    coreir_to_nx,
    coreir_to_pdf,
    nx_to_smt,
)
from memory_core.memtile_util import LakeCoreBase
import time
import os
import sys
import pono
from simple_colors import *
import re
from tabulate import tabulate
from verified_agile_hardware.solver import Solver


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

    for flush in solver.flushes:
        solver.fts.add_invar(
            solver.create_term(
                solver.ops.Equal, flush, solver.create_term(0, flush.get_sort())
            )
        )

    # rst_times = [0, 1]
    # for rst in solver.rsts:
    #     if rst in solver.fts.inputvars:
    #         solver.fts.promote_inputvar(rst)
    #     solver.fts.constrain_init(
    #         solver.create_term(
    #             solver.ops.Equal, rst, solver.create_term(0, rst.get_sort())
    #         )
    #     )
    #     solver.fts_assert_at_times(
    #         rst,
    #         solver.create_term(0, rst.get_sort()),
    #         solver.create_term(1, rst.get_sort()),
    #         rst_times,
    #     )

    # flush_times = [2, 3]
    # for flush in solver.flushes:
    #     if flush in solver.fts.inputvars:
    #         solver.fts.promote_inputvar(flush)
    #     solver.fts.constrain_init(
    #         solver.create_term(
    #             solver.ops.Equal, flush, solver.create_term(0, flush.get_sort())
    #         )
    #     )
    #     solver.fts_assert_at_times(
    #         flush,
    #         solver.create_term(1, flush.get_sort()),
    #         solver.create_term(0, flush.get_sort()),
    #         flush_times,
    #     )


def synchronize_cycle_counts(solver):

    solver.fts.add_invar(
        solver.create_term(
            solver.ops.And,
            solver.create_term(
                solver.ops.BVSgt, solver.cycle_count, solver.create_term(0, solver.cycle_count.get_sort())
            ),
            solver.create_term(
                solver.ops.BVSlt, solver.cycle_count, solver.create_term(1000, solver.cycle_count.get_sort())
            )
        )
    )

    for name, term in solver.fts.named_terms.items():
        if "cycle_count" in name and not solver.fts.is_next_var(term):
            solver.fts.add_invar(
                solver.create_term(solver.ops.Equal, term, solver.cycle_count)
            )

    # for name, term in solver.fts.named_terms.items():
    #     if "dim_counter" in name and not solver.fts.is_next_var(term):
    #         solver.fts.constrain_init(
    #             solver.create_term(solver.ops.Equal, term, solver.create_term(0, term.get_sort()))
    #         )


def flatten(lst):
    result = []
    for i in lst:
        if isinstance(i, list):
            result.extend(flatten(i))
        else:
            result.append(i)
    return result


def set_inputs(solver, input_symbols, halide_image_symbols, bvsort16):

    input_pixel_array = solver.create_fts_state_var("input_pixel_array", solver.solver.make_sort(solver.sortkinds.ARRAY, bvsort16, bvsort16))

    for pix_idx, pix in enumerate(flatten(halide_image_symbols)):
        # set pix to pix_idx
        solver.fts.add_invar(
            solver.create_term(
                solver.ops.Equal, pix, solver.create_term(pix_idx, bvsort16)
            )
        )


        input_pixel_array = solver.create_term(solver.ops.Store, 
                                input_pixel_array, 
                                solver.create_term(pix_idx, solver.create_bvsort(16)), 
                                pix
                            )


    for input_var in input_symbols.values():
        solver.fts.add_invar(
            solver.create_term(
                solver.ops.Equal, 
                    input_var, 
                    solver.create_term(solver.ops.Select, input_pixel_array, solver.cycle_count)
            )
        )

        # solver.fts.constrain_init(
        #     solver.create_term(
        #         solver.ops.Equal, input_var, flatten(halide_image_symbols)[0]
        #     )
        # )
        
        # ite = flatten(halide_image_symbols)[0]
        # time_unrolling = 0

        # for elem in flatten(halide_image_symbols):
        #     is_time = solver.fts.make_term(
        #         solver.ops.Equal,
        #         solver.cycle_count,
        #         solver.create_term(time_unrolling, bvsort16),
        #     )
        #     time_unrolling += 1
        #     ite = solver.fts.make_term(solver.ops.Ite, is_time, elem, ite)

        # solver.fts.add_invar(
        #     solver.create_term(
        #         solver.ops.Equal, input_var, ite
        #     )
        # )



def create_property_term(
    solver, output_symbols, mapped_output_datas, halide_out_symbols, input_to_output_cycle_dep, bvsort16, bvsort1
):

    starting_cycle_count = solver.create_fts_state_var(
        "starting_cycle_count", bvsort16
    )

    solver.fts.constrain_init(
        solver.create_term(
            solver.ops.Equal, starting_cycle_count, solver.cycle_count
        )
    )

    solver.fts.assign_next(
        starting_cycle_count,
        starting_cycle_count
    )

    output_pixel_array = solver.create_fts_state_var("output_pixel_array", solver.solver.make_sort(solver.sortkinds.ARRAY, bvsort16, bvsort16))

    for pix_idx, pix in enumerate(flatten(halide_out_symbols)):
        output_pixel_array = solver.create_term(solver.ops.Store, 
                                output_pixel_array, 
                                solver.create_term(pix_idx, solver.create_bvsort(16)), 
                                pix
                            )

    property_term = solver.create_term(
        solver.ops.Equal,
        solver.create_term(0, bvsort16),
        solver.create_term(0, bvsort16),
    )

    for mapped_output_var_name in mapped_output_datas:
        mapped_output_var = output_symbols[mapped_output_var_name]

        valid_name = f'{mapped_output_var_name.split("_write")[0]}_write_valid'
        assert valid_name in output_symbols
        mapped_valid = output_symbols[valid_name]

        valid_eq = solver.create_term(
            solver.ops.Equal, mapped_valid, solver.create_term(1, bvsort1)
        )

        clk_low = solver.create_term(
            solver.ops.Equal, solver.clks[0], solver.create_term(0, bvsort1)
        )

        valid_and_clk_low = solver.create_term(solver.ops.And, valid_eq, clk_low)

        for i in range(input_to_output_cycle_dep):
            output_dep_on_input = solver.create_term(
                solver.ops.Or,
                solver.create_term(
                    solver.ops.Equal,
                    solver.bmc_counter,
                    solver.create_term(2*i, bvsort16),
                ),
                solver.create_term(
                    solver.ops.Equal,
                    solver.bmc_counter,
                    solver.create_term((2*i) + 1, bvsort16),
                ),
            )

            valid_and_clk_low = solver.create_term(
                solver.ops.And, valid_and_clk_low, solver.create_term(solver.ops.Not, output_dep_on_input)
            )

        halide_pixel_index_var = solver.create_symbol(
            f"halide_pixel_index_{str(mapped_output_var_name)}", bvsort16
        )
        # solver.fts.constrain_init(
        #     solver.create_term(
        #         solver.ops.Equal, out_pixel_count, starting_cycle_count
        #     )
        # )
        # count_plus_one = solver.create_term(
        #     solver.ops.BVAdd, out_pixel_count, solver.create_term(1, bvsort16)
        # )
        # solver.fts.assign_next(
        #     out_pixel_count,
        #     solver.create_term(
        #         solver.ops.Ite, valid_and_clk_low, count_plus_one, out_pixel_count
        #     ),
        # )

        # # Output symbol decoder
        # # This will requiring knowing the order of the output pixels
        # out_symbol_decoder = flatten(halide_out_symbols)[0]
        # output_var_idx = 0
        # for halide_symbol in flatten(halide_out_symbols):
        #     count_eq = solver.create_term(
        #         solver.ops.Equal,
        #         out_pixel_count,
        #         solver.create_term(output_var_idx, bvsort16),
        #     )
        #     out_symbol_decoder = solver.create_term(
        #         solver.ops.Ite, count_eq, halide_symbol, out_symbol_decoder
        #     )
        #     output_var_idx += 1

        # Use stencil valid memtile addr_out - cycle_starting_addr as the index for the output_pixel_array
        assert valid_name in solver.stencil_valid_to_port_controller
        memtile = solver.stencil_valid_to_port_controller[valid_name]
        for name, term in solver.fts.named_terms.items():
            if "addr_out" in name and memtile in name and not solver.fts.is_next_var(term):
                addr_out = term
                break

        halide_pixel_index = solver.create_term(
            solver.ops.BVSub, addr_out, starting_cycle_count
        )

        solver.fts.add_invar(
            solver.create_term(
                solver.ops.Equal, halide_pixel_index, halide_pixel_index_var
            )
        )

        halide_out = solver.create_fts_state_var(
            f"halide_out_{str(mapped_output_var_name)}", bvsort16
        )

        solver.fts.add_invar(
            solver.create_term(
                solver.ops.Equal, halide_out, solver.create_term(solver.ops.Select, output_pixel_array, halide_pixel_index)
            )
        )

        data_eq = solver.create_term(
            solver.ops.Equal, mapped_output_var, halide_out
        )

        out_symbol_data_eq = solver.create_fts_state_var(
            f"out_symbol_data_eq_{str(mapped_output_var_name)}", data_eq.get_sort()
        )
        solver.fts.add_invar(
            solver.create_term(solver.ops.Equal, out_symbol_data_eq, data_eq)
        )

        imp = solver.create_term(solver.ops.Implies, valid_eq, data_eq)

        property_term = solver.create_term(solver.ops.And, property_term, imp)


    for i in range(input_to_output_cycle_dep):
        output_dep_on_input = solver.create_term(
            solver.ops.Or,
            solver.create_term(
                solver.ops.Equal,
                solver.bmc_counter,
                solver.create_term(2*i, bvsort16),
            ),
            solver.create_term(
                solver.ops.Equal,
                solver.bmc_counter,
                solver.create_term((2*i) + 1, bvsort16),
            ),
        )

        property_term = solver.create_term(
            solver.ops.Or,
            output_dep_on_input,
            property_term
        )

    return property_term


def print_trace(solver, bmc, symbols, waveform_signals=[]):
    print("Counterexample found")

    named_terms_reversed = {v: k for k, v in solver.fts.named_terms.items()}

    trace_table = []

    trace = ["0step"]
    trace += list(range(len(bmc.witness())))
    trace_table.append(trace)

    trace = ["1clock"]
    t = list(range(len(bmc.witness())))
    trace += [int(n / 2) for n in t]
    trace_table.append(trace)


    witnesses = bmc.witness()
    for var, _ in witnesses[0].items():
        name = str(var)
        display = False

        if var in named_terms_reversed:
            name = named_terms_reversed[var]
            for signal in waveform_signals:
                if signal in name:
                    display = True

        if str(var) in symbols:
            display = True

        if "next" in str(var):
            display = False

        if display:
            trace = [name]
            for witness in witnesses:
                val = witness[var]

                if "bv" in str(val):
                    val = int(re.split("bv(\d*)", str(val))[1].strip())
                    val = (val + 2**15) % 2**16 - 2**15

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


def run_bmc_profiling_sweep(solver, prop):
    bmc_checks = [1, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100]
    # bmc_checks = [400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500]
    # for bmc_check in bmc_checks:
    #     btor_solver = Solver(solver_name = "cvc5")
    #     bmc = pono.Bmc(prop, solver.fts, btor_solver.solver)
    #     # print("Running BMC...")
    #     start = time.time()
    #     res = bmc.check_until(bmc_check*2)
    #     print(bmc_check, time.time() - start)

    # for bmc_check in bmc_checks:
    #     btor_solver = Solver(solver_name="bitwuzla")
    #     bmc = pono.Bmc(prop, solver.fts, btor_solver.solver)
    #     # print("Running BMC...")
    #     start = time.time()
    #     res = bmc.check_until(bmc_check * 2)
    #     print(bmc_check, time.time() - start)

    for bmc_check in bmc_checks:
        btor_solver = Solver(solver_name = "btor")
        bmc = pono.Bmc(prop, solver.fts, btor_solver.solver)
        # print("Running BMC...")
        start = time.time()
        res = bmc.check_until(bmc_check*2)
        print(bmc_check, time.time() - start)
        assert res is None or res


def import_from(module, name):
    module = __import__(module, fromlist=[name])
    return getattr(module, name)


def verify_design_top(interconnect, coreir_file):
    file_info = {}
    file_info["port_remapping"] = coreir_file.replace(
        "design_top.json", "design.port_remap"
    )
    app_dir = os.path.dirname(coreir_file)

    nx = coreir_to_nx(read_coreir(coreir_file))

    # Instantiate solver object
    solver = Solver()
    solver.solver.set_opt("produce-models", "true")
    solver.file_info = file_info
    solver.app_dir = f"{app_dir}/verification"

    solver, input_symbols, output_symbols = nx_to_smt(nx, interconnect, solver, app_dir)

    set_clk_rst_flush(solver)

    synchronize_cycle_counts(solver)

    bvsort16 = solver.create_bvsort(16)
    bvsort1 = solver.create_bvsort(1)

    mapped_output_datas = []
    mapped_output_valids = []

    for output_var in output_symbols.keys():
        if "valid" == str(output_var)[-5:]:
            mapped_output_valids.append(output_var)
        else:
            mapped_output_datas.append(output_var)

    sys.path.append(os.path.abspath(app_dir))

    create_app = import_from(
        f"{app_dir.split(os.sep)[-2]}_pono_testbench", "create_app"
    )

    hw_input_stencil, hw_output_stencil = create_app(solver)

    set_inputs(solver, input_symbols, hw_input_stencil, bvsort16)


    # Is this right? May not be general 
    input_to_output_cycle_dep = solver.first_valid_output

    property_term = create_property_term(
        solver,
        output_symbols,
        mapped_output_datas,
        hw_output_stencil,
        input_to_output_cycle_dep,
        bvsort16,
        bvsort1,
    )

    prop = pono.Property(solver.solver, property_term)

    btor_solver = Solver(solver_name="btor")
    bmc = pono.Bmc(prop, solver.fts, btor_solver.solver)

    #run_bmc_profiling_sweep(solver, prop)

    #breakpoint()

    check_pixels = 1
    check_cycles = solver.first_valid_output + 1 + check_pixels

    print("First valid output at cycle", solver.first_valid_output)
    print("Running BMC for", check_cycles, "cycles")
    start = time.time()
    res = bmc.check_until(check_cycles * 2)
    print(time.time() - start)

    if res is None or res:

        # Create property term that says valid is always 0
        property_term = solver.create_term(
            solver.ops.Equal,
            solver.create_term(0, bvsort16),
            solver.create_term(0, bvsort16),
        )

        for mapped_output_var_name in mapped_output_valids:
            mapped_output_var = output_symbols[mapped_output_var_name]

            valid_eq = solver.create_term(
                solver.ops.Equal, mapped_output_var, solver.create_term(0, bvsort1)
            )

            property_term = solver.create_term(solver.ops.And, property_term, valid_eq)

        prop = pono.Property(solver.solver, property_term)
        btor_solver = Solver(solver_name="btor")
        bmc = pono.Bmc(prop, solver.fts, btor_solver.solver)

        print("Running BMC for", check_cycles, "cycles")
        start = time.time()
        res2 = bmc.check_until(check_cycles * 2)
        print(time.time() - start)

        if res2 is None or res2:
            print("\n\033[91m" + "Valid is never high" + "\033[0m")
        else:
            print("\n\033[92m" + "Formal check of mapped application passed" + "\033[0m")

    else:
        
        waveform_signals = [
            "in.hw_input",
            "halide_pixel_index_",
            "out_symbol_data_eq_",
            "in_symbol_",
            "flush",
            "cycle_count",
            'addr_out', 
            'halide_out',
            "dim_counter"
        ]

        symbols = mapped_output_datas + mapped_output_valids
        
        print_trace(solver, bmc, symbols, waveform_signals)

    breakpoint()
