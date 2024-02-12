from verified_agile_hardware.coreir_utils import (
    read_coreir,
    coreir_to_nx,
    coreir_to_pdf,
    nx_to_smt,
)
from memory_core.memtile_util import LakeCoreBase
import time
import os
import pono
from simple_colors import *
import re
from tabulate import tabulate


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


def set_inputs(solver, input_symbols, halide_image_symbols, bvsort16):
    # for input_var in input_symbols.values():
    #     solver.fts.constrain_init(solver.create_term(solver.ops.Equal, input_var, solver.create_term(5, bvsort16)))
    #     solver.fts.assign_next(input_var, input_var)

    # for row in halide_image_symbols:
    #     for elem in row:
    #         solver.fts.add_invar(solver.create_term(solver.ops.Equal, elem, solver.create_term(5, bvsort16)))

    for input_var in input_symbols.values():
        solver.fts.constrain_init(
            solver.create_term(
                solver.ops.Equal, input_var, solver.create_term(0, bvsort16)
            )
        )
        ite = halide_image_symbols[0][0]
        conv_var_unroll = 3
        for row_conv in halide_image_symbols:
            for conv_var in row_conv:
                is_time = solver.fts.make_term(
                    solver.ops.Or,
                    solver.fts.make_term(
                        solver.ops.Equal,
                        solver.bmc_counter,
                        solver.create_term(conv_var_unroll, bvsort16),
                    ),
                    solver.fts.make_term(
                        solver.ops.Equal,
                        solver.bmc_counter,
                        solver.create_term(conv_var_unroll + 1, bvsort16),
                    ),
                )
                conv_var_unroll += 2
                ite = solver.fts.make_term(solver.ops.Ite, is_time, conv_var, ite)

        solver.fts.assign_next(input_var, ite)


def create_property_term(
    solver, output_symbols, mapped_output_datas, halide_out_symbols, bvsort16, bvsort1
):
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

        out_pixel_count = solver.create_fts_state_var(
            f"out_count_{str(mapped_output_var_name)}", bvsort16
        )
        solver.fts.constrain_init(
            solver.create_term(
                solver.ops.Equal, out_pixel_count, solver.create_term(0, bvsort16)
            )
        )
        count_plus_one = solver.create_term(
            solver.ops.BVAdd, out_pixel_count, solver.create_term(1, bvsort16)
        )
        solver.fts.assign_next(
            out_pixel_count,
            solver.create_term(
                solver.ops.Ite, valid_and_clk_low, count_plus_one, out_pixel_count
            ),
        )

        # Output symbol decoder
        # This will requiring knowing the order of the output pixels
        out_symbol_decoder = halide_out_symbols[0][0]
        output_var_idx = 0
        for output_var_row in halide_out_symbols:
            for output_var in output_var_row:
                count_eq = solver.create_term(
                    solver.ops.Equal,
                    out_pixel_count,
                    solver.create_term(output_var_idx, bvsort16),
                )
                out_symbol_decoder = solver.create_term(
                    solver.ops.Ite, count_eq, output_var, out_symbol_decoder
                )
                output_var_idx += 1

        out_symbol_decoder_var = solver.create_fts_state_var(
            f"out_symbol_decoder_{str(mapped_output_var_name)}", bvsort16
        )

        solver.fts.add_invar(
            solver.create_term(
                solver.ops.Equal, out_symbol_decoder_var, out_symbol_decoder
            )
        )

        data_eq = solver.create_term(
            solver.ops.Equal, mapped_output_var, out_symbol_decoder
        )

        out_symbol_data_eq = solver.create_fts_state_var(
            f"out_symbol_data_eq_{str(mapped_output_var_name)}", data_eq.get_sort()
        )
        solver.fts.add_invar(
            solver.create_term(solver.ops.Equal, out_symbol_data_eq, data_eq)
        )

        imp = solver.create_term(solver.ops.Implies, valid_eq, data_eq)

        property_term = solver.create_term(solver.ops.And, property_term, imp)
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


def verify_design_top(interconnect, coreir_file):
    file_info = {}
    file_info["port_remapping"] = coreir_file.replace(
        "design_top.json", "design.port_remap"
    )
    app_dir = os.path.dirname(coreir_file) # coreir_file has mapped dataflow graph

    nx = coreir_to_nx(read_coreir(coreir_file)) # translate coreir to network x
    solver, input_symbols, output_symbols = nx_to_smt(
        nx, interconnect, file_info, app_dir
    ) # network x to SMT

    set_clk_rst_flush(solver)

    bvsort16 = solver.create_bvsort(16)
    bvsort1 = solver.create_bvsort(1)

    mapped_output_datas = []
    mapped_output_valids = []

    for output_var in output_symbols.keys():
        if "valid" == str(output_var)[-5:]:
            mapped_output_valids.append(output_var)
        else:
            mapped_output_datas.append(output_var)

    halide_image_symbols, halide_kernel_symbols, halide_out_symbols = create_conv_smt(
        solver
    )

    idx = 0
    for row in halide_kernel_symbols:
        for elem in row:
            solver.fts.add_invar(
                solver.create_term(
                    solver.ops.Equal, elem, solver.create_term(1, bvsort16)
                )
            )
            idx += 1

    idx = 0
    for row in halide_image_symbols:
        for elem in row:
            solver.fts.add_invar(
                solver.create_term(
                    solver.ops.Equal, elem, solver.create_term(idx, bvsort16)
                )
            )
            idx += 1

    set_inputs(solver, input_symbols, halide_image_symbols, bvsort16)
    # set input symbols of mapped and unmapped equal

    property_term = create_property_term(
        solver,
        output_symbols,
        mapped_output_datas,
        halide_out_symbols,
        bvsort16,
        bvsort1,
    )

    prop = pono.Property(solver.solver, property_term) # create property

    print(prop.prop)

    bmc = pono.Bmc(prop, solver.fts, solver.solver) # run bmc checker

    print("Running BMC...")
    start = time.time()
    res = bmc.check_until(200)
    print("BMC time:", time.time() - start)

    if res is None or res:
        print("\n\033[92m" + "Formal check of mapped application passed" + "\033[0m")
    else:
        print_trace(bmc, mapped_output_datas, mapped_output_valids)

    breakpoint()
