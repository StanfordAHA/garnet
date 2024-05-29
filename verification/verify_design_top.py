from verified_agile_hardware.coreir_utils import (
    read_coreir,
    coreir_to_nx,
    nx_to_pdf,
    nx_to_smt,
)

from verified_agile_hardware.lake_utils import mem_tile_get_num_valids
from memory_core.memtile_util import LakeCoreBase
import time
import os
import sys
import pono
from simple_colors import *
import re
from tabulate import tabulate
from verified_agile_hardware.solver import Solver
import smt_switch as ss
import multiprocessing
import math


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

    for name, term in solver.fts.named_terms.items():
        if "valid_gate_inv" in name and not solver.fts.is_next_var(term):
            solver.fts.constrain_init(
                solver.create_term(
                    solver.ops.Equal, term, solver.create_term(0, term.get_sort())
                )
            )
        if "flushed" in name and not solver.fts.is_next_var(term):
            solver.fts.constrain_init(
                solver.create_term(
                    solver.ops.Equal, term, solver.create_term(1, term.get_sort())
                )
            )


def synchronize_cycle_counts(solver):

    # cycle_count_in_range = solver.create_term(
    #     solver.ops.And,
    #     solver.create_term(
    #         solver.ops.BVSge,
    #         solver.cycle_count,
    #         solver.create_term(0, solver.cycle_count.get_sort()),
    #     ),
    #     solver.create_term(
    #         solver.ops.BVSlt,
    #         solver.cycle_count,
    #         solver.create_term(solver.max_cycles, solver.cycle_count.get_sort()),
    #     ),
    # )

    # solver.fts.add_invar(cycle_count_in_range)

    for name, term in solver.fts.named_terms.items():
        if "cycle_count" in name and not solver.fts.is_next_var(term):
            solver.fts.add_invar(
                solver.create_term(solver.ops.Equal, term, solver.cycle_count)
            )

    print("Constraining cycle count to start at starting_cycle")
    solver.fts.constrain_init(
        solver.create_term(
            solver.ops.Equal,
            solver.cycle_count,
            solver.create_term(solver.starting_cycle, solver.cycle_count.get_sort()),
        )
    )


def flatten(lst):
    result = []
    for i in lst:
        if isinstance(i, list):
            result.extend(flatten(i))
        else:
            result.append(i)
    return result


def set_inputs(solver, pnr_symbols, halide_ins_and_outs, matched_inputs, bvsort16):

    # print("set pix to pix_idx")
    # for pix_idx, pix in enumerate(flatten(halide_image_symbols)):
    #     solver.fts.add_invar(
    #         solver.create_term(
    #             solver.ops.Equal, pix, solver.create_term(pix_idx, bvsort16)
    #         )
    #     )

    for halide_name, pnr_names in matched_inputs.items():

        halide_symbols = halide_ins_and_outs[halide_name]

        input_pnr_unrolling = len(pnr_names)

        starting_index = input_pnr_unrolling * solver.starting_cycle
        ending_index = (input_pnr_unrolling * solver.max_cycles) + input_pnr_unrolling

        lut_vals = []
        for pix_idx, pix in enumerate(flatten(halide_symbols)):
            lut_vals.append((solver.create_const(pix_idx, bvsort16), pix))

        input_pixel = solver.create_lut(
            "input_pixel_array_" + halide_name,
            lut_vals,
            bvsort16,
            bvsort16,
            starting_index,
            ending_index,
        )

        for index in range(solver.starting_cycle, solver.max_cycles):
            if not input_pixel(
                solver.create_const(index, bvsort16)
            ).is_symbolic_const():
                print(
                    "Input pixel",
                    index,
                    input_pixel(solver.create_const(index, bvsort16)),
                )

        for pnr_idx, pnr_name in enumerate(pnr_names):
            pnr_symbol = pnr_symbols[pnr_name]
            index = solver.create_term(
                solver.ops.BVAdd,
                solver.create_term(
                    solver.ops.BVMul,
                    solver.cycle_count,
                    solver.create_term(len(pnr_names), solver.cycle_count.get_sort()),
                ),
                solver.create_term(pnr_idx, solver.cycle_count.get_sort()),
            )
            solver.fts.add_invar(
                solver.create_term(
                    solver.ops.Equal,
                    pnr_symbol,
                    input_pixel(index),
                )
            )

    # print(len(solver.fts.named_terms), len(solver.fts.statevars), len(str(solver.fts.trans)))


def create_property_term(
    solver,
    output_symbols,
    mapped_output_datas,
    halide_ins_and_outs,
    halide_to_mapped_outputs,
    input_to_output_cycle_dep,
    bvsort16,
    bvsort1,
):

    for halide_out, pnr_outputs in halide_to_mapped_outputs.items():
        halide_out_symbols = halide_ins_and_outs[halide_out]

        lut_vals = []
        for pix_idx, pix in enumerate(flatten(halide_out_symbols)):
            lut_vals.append((solver.create_const(pix_idx, bvsort16), pix))

        starting_index = 0
        ending_index = (len(pnr_outputs) * solver.max_cycles) + len(pnr_outputs)

        output_pixel_array = solver.create_lut(
            "output_pixel_array_" + halide_out,
            lut_vals,
            bvsort16,
            bvsort16,
            starting_index,
            ending_index,
        )

        property_term = solver.create_term(True)

        for output_var_idx, mapped_output_var_name in enumerate(pnr_outputs):
            mapped_output_var = output_symbols[mapped_output_var_name]

            valid_name = (
                f'{mapped_output_var_name.split("_write")[0]}_write_valid'.replace(
                    "io16", "io1"
                ).replace("io17", "io1")
            )
            assert valid_name in output_symbols
            mapped_valid = output_symbols[valid_name]

            valid_eq = solver.create_term(
                solver.ops.Equal, mapped_valid, solver.create_term(1, bvsort1)
            )

            halide_pixel_index_var = solver.create_fts_state_var(
                f"halide_pixel_index_{str(mapped_output_var_name)}", bvsort16
            )

            # Precalculate the halide pixel index based on the memory tile schedule
            assert valid_name in solver.stencil_valid_to_port_controller
            memtile = solver.stencil_valid_to_port_controller[valid_name]

            # This is a list that stores the number of valid pixels at each cycle
            # Can use this to index into halide output pixel array
            cycle_to_halide_idx, valids = mem_tile_get_num_valids(
                solver.stencil_valid_to_schedule[memtile],
                solver.max_cycles,
                iterator_support=6,
            )

            cycle_to_halide_lut = []
            for i, idx in enumerate(cycle_to_halide_idx):
                cycle_to_halide_lut.append(
                    (
                        solver.create_const(i, bvsort16),
                        solver.create_const(idx, bvsort16),
                    )
                )

            cycle_to_halide_idx_var = solver.create_lut(
                f"{memtile}_cycle_to_halide_idx_lut",
                cycle_to_halide_lut,
                bvsort16,
                bvsort16,
                solver.starting_cycle,
                solver.max_cycles,
            )

            halide_pixel_index = cycle_to_halide_idx_var(solver.cycle_count)

            halide_pixel_index = solver.create_term(
                solver.ops.BVAdd,
                solver.create_term(
                    solver.ops.BVMul,
                    halide_pixel_index,
                    solver.create_term(
                        len(mapped_output_datas), halide_pixel_index.get_sort()
                    ),
                ),
                solver.create_term(output_var_idx, halide_pixel_index.get_sort()),
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
                    solver.ops.Equal,
                    halide_out,
                    output_pixel_array(halide_pixel_index),
                )
            )

            # solver.fts.assign_next(halide_out, output_pixel_array(halide_pixel_index))

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

    print("input_to_output_cycle_dep", input_to_output_cycle_dep)

    # If solver.bmc_counter is less than to solver.first_valid_output
    output_dep_on_input = solver.create_term(
        solver.ops.BVUle,
        solver.bmc_counter,
        solver.create_term(2 * input_to_output_cycle_dep, bvsort16),
    )

    property_term = solver.create_term(
        solver.ops.Or, output_dep_on_input, property_term
    )

    return property_term


def create_valids_property_term(
    solver,
    output_symbols,
    mapped_output_datas,
    bvsort16,
    bvsort1,
):

    property_term = solver.create_term(True)

    for mapped_output_var_name in mapped_output_datas:
        mapped_output_var = output_symbols[mapped_output_var_name]

        valid_name = f'{mapped_output_var_name.split("_write")[0]}_write_valid'.replace(
            "io16", "io1"
        ).replace("io17", "io1")
        assert valid_name in output_symbols
        mapped_valid = output_symbols[valid_name]

        halide_valid_sym = solver.create_fts_state_var(
            f"halide_valid_{str(mapped_output_var_name)}", bvsort1
        )

        # Precalculate the halide pixel index based on the memory tile schedule
        assert valid_name in solver.stencil_valid_to_port_controller, breakpoint()
        memtile = solver.stencil_valid_to_port_controller[valid_name]

        # This is a list that stores the number of valid pixels at each cycle
        # Can use this to index into halide output pixel array
        cycle_to_halide_idx, valids = mem_tile_get_num_valids(
            solver.stencil_valid_to_schedule[memtile],
            solver.max_cycles,
            iterator_support=6,
        )

        cycle_to_halide_idx_lut = []
        for i, idx in enumerate(valids):
            cycle_to_halide_idx_lut.append(
                (solver.create_const(i, bvsort16), solver.create_const(idx, bvsort1))
            )

        cycle_to_halide_idx_var = solver.create_lut(
            f"{memtile}_cycle_to_halide_idx_valids_var",
            cycle_to_halide_idx_lut,
            bvsort16,
            bvsort1,
            solver.starting_cycle,
            solver.max_cycles,
        )

        halide_valid = cycle_to_halide_idx_var(solver.cycle_count)

        solver.fts.add_invar(
            solver.create_term(solver.ops.Equal, halide_valid_sym, halide_valid)
        )

        property_term = solver.create_term(
            solver.ops.And,
            property_term,
            solver.create_term(solver.ops.Equal, mapped_valid, halide_valid),
        )

    return property_term


def create_cycle_count_property_term(
    solver,
    bvsort16,
):
    # Create property term that says cycle count incremements every 2 bmc counters
    check_cycle_count = solver.create_fts_state_var("check_cycle_count", bvsort16)

    solver.fts.constrain_init(
        solver.create_term(solver.ops.Equal, solver.cycle_count, check_cycle_count)
    )

    solver.fts.assign_next(
        check_cycle_count,
        solver.create_term(
            solver.ops.Ite,
            solver.create_term(
                solver.ops.Equal,
                solver.create_term(
                    solver.ops.BVUrem,
                    solver.bmc_counter,
                    solver.create_term(2, solver.bmc_counter.get_sort()),
                ),
                solver.create_term(1, solver.bmc_counter.get_sort()),
            ),
            solver.create_term(
                solver.ops.BVAdd,
                check_cycle_count,
                solver.create_term(1, check_cycle_count.get_sort()),
            ),
            check_cycle_count,
        ),
    )

    property_term = solver.create_term(
        solver.ops.Equal, solver.cycle_count, check_cycle_count
    )

    return property_term


def print_trace(solver, bmc, symbols, waveform_signals=[]):
    print("Counterexample found")

    named_terms_reversed = {v: k for k, v in solver.fts.named_terms.items()}

    trace_table = []

    trace = ["step"]
    trace += list(range(len(bmc.witness())))
    trace_table.append(trace)

    trace = ["clock"]
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

                if "#b" in str(val):
                    val = str(val).replace("#b", "")
                    val = int(val, 2)

                if "false" in str(val):
                    trace.append(red("0"))
                elif "true" in str(val):
                    trace.append(green("1"))
                elif int(str(val)) == 0:
                    trace.append(red(str(val)))
                else:
                    trace.append(green(str(val)))

            trace_table.append(trace)
    trace_table_sorted = []
    trace_table_sorted.append(trace_table[0])
    trace_table_sorted.append(trace_table[1])

    for symbol in symbols:
        for trace in trace_table:
            if str(symbol) == trace[0]:
                trace_table_sorted.append(trace)

    for symbol in waveform_signals:
        for trace in trace_table:
            if str(symbol) in trace[0]:
                trace_table_sorted.append(trace)

    print(tabulate(trace_table_sorted))


def check_if_fts_overconstrained(solver):
    prop = pono.Property(solver.solver, solver.create_term(False))
    btor_solver = Solver(solver_name="btor")
    bmc = pono.Bmc(prop, solver.fts, btor_solver.solver)
    res = bmc.check_until(1)

    if res is None:
        print("\033[91m" + "FTS is overconstrained" + "\033[0m")
        exit(1)


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
        btor_solver = Solver(solver_name="btor")
        bmc = pono.Bmc(prop, solver.fts, btor_solver.solver)
        # print("Running BMC...")
        start = time.time()
        res = bmc.check_until(bmc_check * 2)
        print(bmc_check, time.time() - start)
        assert res is None or res


def import_from(module, name):
    module = __import__(module, fromlist=[name])
    return getattr(module, name)


def verify_design_top_parallel(
    interconnect, coreir_file, starting_cycle=0, ending_cycle=100
):
    print("Checking pixels", starting_cycle, "to", ending_cycle)

    file_info = {}
    file_info["port_remapping"] = coreir_file.replace(
        "design_top_map.json", "design.port_remap"
    )
    app_dir = os.path.dirname(coreir_file)

    nx = coreir_to_nx(read_coreir(coreir_file))

    # Instantiate solver object
    solver = Solver()

    solver.starting_cycle = starting_cycle
    solver.max_cycles = ending_cycle

    sys.path.append(os.path.abspath(app_dir))

    create_app = import_from(
        f"{app_dir.split(os.sep)[-2]}_pono_testbench", "create_app"
    )

    halide_ins_and_outs = create_app(Solver())

    solver.solver.set_opt("produce-models", "true")

    solver.file_info = file_info
    solver.app_dir = f"{app_dir}/verification_{starting_cycle}"

    solver, input_symbols, output_symbols = nx_to_smt(nx, interconnect, solver)

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

    halide_to_mapped_inputs = {}
    halide_to_mapped_outputs = {}

    for k in halide_ins_and_outs.keys():
        for m in sorted(list(input_symbols.keys())):
            if k in m:
                if k not in halide_to_mapped_inputs:
                    halide_to_mapped_inputs[k] = []
                halide_to_mapped_inputs[k].append(m)

    for k in halide_ins_and_outs.keys():
        for m in sorted(list(mapped_output_datas)):
            if k in m:
                if k not in halide_to_mapped_outputs:
                    halide_to_mapped_outputs[k] = []
                halide_to_mapped_outputs[k].append(m)

    if len(halide_to_mapped_outputs) == 0:
        for k in halide_ins_and_outs.keys():
            k_new = k.replace("stencil", "")
            for m in sorted(list(mapped_output_datas)):
                if k_new in m:
                    if k not in halide_to_mapped_outputs:
                        halide_to_mapped_outputs[k] = []
                    halide_to_mapped_outputs[k].append(m)

    print(halide_to_mapped_inputs)
    print(halide_to_mapped_outputs)

    input_pnr_unrolling = 1
    for halide_name, pnr_names in halide_to_mapped_inputs.items():
        input_pnr_unrolling = max(input_pnr_unrolling, len(pnr_names))

    starting_index = input_pnr_unrolling * solver.starting_cycle
    ending_index = (input_pnr_unrolling * solver.max_cycles) + input_pnr_unrolling

    halide_ins_and_outs = create_app(solver, starting_index, ending_index)

    print("Setting input constraints")
    set_inputs(
        solver, input_symbols, halide_ins_and_outs, halide_to_mapped_inputs, bvsort16
    )

    input_to_output_cycle_dep = solver.first_valid_output

    print("Creating property term")
    cycle_count_property_term = create_cycle_count_property_term(
        solver,
        bvsort16,
    )

    valids_property_term = create_valids_property_term(
        solver,
        output_symbols,
        mapped_output_datas,
        bvsort16,
        bvsort1,
    )

    property_term = create_property_term(
        solver,
        output_symbols,
        mapped_output_datas,
        halide_ins_and_outs,
        halide_to_mapped_outputs,
        input_to_output_cycle_dep,
        bvsort16,
        bvsort1,
    )

    property_term = solver.create_term(
        solver.ops.And, property_term, valids_property_term
    )
    property_term = solver.create_term(
        solver.ops.And, property_term, cycle_count_property_term
    )

    check_if_fts_overconstrained(solver)

    prop = pono.Property(solver.solver, property_term)

    print("Named terms", len(solver.fts.named_terms))
    print("State vars", len(solver.fts.statevars))
    print("Trans size", len(str(solver.fts.trans)))

    # btor_solver = Solver(solver_name="btor")
    btor_solver = solver
    bmc = pono.Bmc(prop, solver.fts, btor_solver.solver)

    check_cycles = solver.max_cycles - solver.starting_cycle

    print("First valid output at cycle", solver.first_valid_output)
    print("Running BMC for", check_cycles, "cycles")
    start = time.time()
    res = bmc.check_until(check_cycles * 2)
    print(time.time() - start)

    if res is None or res:

        # # Create property term that says valid is always 0
        # property_term = solver.create_term(True)

        # for mapped_output_var_name in mapped_output_valids:
        #     mapped_output_var = output_symbols[mapped_output_var_name]

        #     valid_eq = solver.create_term(
        #         solver.ops.Equal, mapped_output_var, solver.create_term(0, bvsort1)
        #     )

        #     property_term = solver.create_term(solver.ops.And, property_term, valid_eq)

        # prop = pono.Property(solver.solver, property_term)
        # btor_solver = Solver(solver_name="btor")
        # bmc = pono.Bmc(prop, solver.fts, btor_solver.solver)

        # print("Running BMC for", check_cycles, "cycles")
        # start = time.time()
        # res2 = bmc.check_until(check_cycles * 2)
        # print(time.time() - start)

        # if res2 is None or res2:
        #     print("\n\033[91m" + "Valid can never be 1" + "\033[0m")
        #     # raise Exception("Counterexample found")
        # else:
        print("\n\033[92m" + "Formal check of mapped application passed" + "\033[0m")
        # return True

    else:

        # vcd_printer = pono.VCDWitnessPrinter(solver.fts, bmc.witness())
        # vcd_printer.dump_trace_to_file("/aha/dense_only.vcd")

        waveform_signals = [
            "halide_pixel_index_",
            "out_symbol_data_eq_",
            "in_symbol_",
            "halide_out",
            "halide_valid",
        ]

        symbols = (
            list(input_symbols.keys())
            + list(output_symbols.keys())
            + ["cycle_count", "bmc_counter", "check_cycle_count"]
        )

        print_trace(solver, bmc, symbols, waveform_signals)

        # raise Exception("Counterexample found")


import concurrent.futures


def get_first_output_from_coreir(coreir_file):

    app_name = coreir_file.split("/")[-3]

    with open(coreir_file, "r") as f:
        lines = f.readlines()

        for line in lines:
            if 'in2glb_0"' in line:
                return int(line.split('cycle_starting_addr":[')[-1].split("]")[0])


def verify_design_top(interconnect, coreir_file):

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
        # verify_design_top_parallel(interconnect, coreir_file, starting_cycle, ending_cycle)
        # print("Checking pixels", starting_cycle, "to", ending_cycle)
        check_pixels.append((starting_cycle, ending_cycle))
        check_pixel += pixels_per_core

    def verify_design_top_parallel_wrapper(args):
        starting_cycle, ending_cycle = args
        print("Checking pixels", starting_cycle, "to", ending_cycle)
        verify_design_top_parallel(
            interconnect, coreir_file, starting_cycle, ending_cycle
        )

    if True:
        results = []
        processes = []
        for check_pixel in check_pixels:
            process = multiprocessing.Process(
                target=verify_design_top_parallel_wrapper, args=(check_pixel,)
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

        # for check_pixel in check_pixels:
        #     verify_design_top_parallel_wrapper(check_pixel)

        # verify_design_top_parallel_wrapper(check_pixels[0])

        if (
            "harris" in coreir_file
            or "unsharp" in coreir_file
            or "gaussian" in coreir_file
        ):
            verify_design_top_parallel_wrapper((0, 500))
        else:
            verify_design_top_parallel_wrapper((0, 200))

    # breakpoint()
