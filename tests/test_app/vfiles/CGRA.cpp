// See /usr/local/share/verilator/examples/make_tracing_c/sim_main.cpp


// DESCRIPTION: Verilator: Verilog example module
//
// This file ONLY is placed under the Creative Commons Public Domain, for
// any use, without warranty, 2017 by Wilson Snyder.
// SPDX-License-Identifier: CC0-1.0
//======================================================================

#include <stdio.h>
#include <stdlib.h>

// For std::unique_ptr
#include <memory>

// Include common routines
#include <verilated.h>

// Include model header, generated from Verilating "top.v"
#include "Vtop.h"
// #include "Vtop_top.h"

// Legacy function required only so linking works on Cygwin and MSVC++
double sc_time_stamp() { return 0; }

// See e.g. /usr/local/share/verilator/examples/make_tracing_c/sim_main.cpp
int main(int argc, char** argv) {

    // '5000' means 5ns. Why? Maybe b/c timescale = 1ps/1ps
    int ns = 1000; int half_ns = ns/2;

    // E.g. "vtop 300" to run for 300ns
    int MAX_NS = 300*ns;
    for (int i=1; i<argc; i++) {
        int maybe_integer = atoi(argv[i]);
        if (maybe_integer > 0) MAX_NS = maybe_integer;
    }
    // MAX_NS += half_ns;  // So we don't end on an edge

    // Create logs/ directory in case we have traces to put under it
    Verilated::mkdir("logs");

    // Construct a VerilatedContext to hold simulation time, etc.

    // Using unique_ptr is similar to
    // "VerilatedContext* contextp = new VerilatedContext" then deleting at end.
    const std::unique_ptr<VerilatedContext> contextp{new VerilatedContext};
    // Do not instead make Vtop as a file-scope static variable, as the
    // "C++ static initialization order fiasco" may cause a crash

    // Set debug level, 0 is off, 9 is highest presently used
    // May be overridden by commandArgs argument parsing
    contextp->debug(0);

    // Randomization reset policy
    // May be overridden by commandArgs argument parsing
    // 0: init to zero; 1: init to 1; 2: init to random
    // contextp->randReset(2);
    contextp->randReset(0);

    // Verilator must compute traced signals
    contextp->traceEverOn(true);

    // Pass arguments so Verilated code can see them, e.g. $value$plusargs
    // This needs to be called before you create any model
    contextp->commandArgs(argc, argv);

    // Construct the Verilated model, from Vtop.h generated from Verilating "top.v".
    // Using unique_ptr is similar to "Vtop* top = new Vtop" then deleting at end.
    // "TOP" will be the hierarchical name of the module.
    const std::unique_ptr<Vtop> top{new Vtop{contextp.get(), "TOP"}};
    /*
    // Set Vtop's input signals
    // top->reset_l = !0;
    // top->clk = 0;
    top->in_small = 1;
    top->in_quad = 0x1234;
    top->in_wide[0] = 0x11111111;
    top->in_wide[1] = 0x22222222;
    top->in_wide[2] = 0x3;
    */
    // Simulate until $finish
    // while (!contextp->gotFinish()) {

    // 80.5 x 1000 = 80 x 100 + 500
    // for (int i=0; i<(80.5*ns); i++) {
    // for (int i=0; i<(210.5*ns); i++) {
    // for (int i=0; i<(MAX_NS*ns); i++) {

    int i=-1;
    while (!contextp->gotFinish()) {
        i++; if (i > MAX_NS*ns) break;  // (Note "i" starts at -1)

    // for (int i=0; i<(1800.5*ns); i++) {
    // for (int i=0; i<(12000.5*ns); i++) {
        // if (contextp->gotFinish()) break;

        bool do_print;

        // if (i <= 10*ns) do_print = !(i % (1*ns));  // Print every ns for first 10ns
        // else do_print = !(i % (10*ns));            // Then every 10ns thereafter
        do_print = !(i % (10*ns));            // Print a timestamp every 10ns maybe
        if (do_print) {
            printf("[%0dns] CGRA.cpp loop # %dK\n", i/ns, i/1000); fflush(stdout);
          //printf("[%0dns] vtop.cpp loop # %dK\n", i/ns, i/1000); fflush(stdout);
        }
        top->eval();
        contextp->timeInc(1);  // 1ps maybe

        ////////////////////////////////////////////////////////////////////////
        /*
        // Toggle a fast (time/2 period) clock
        top->clk = !top->clk;
        // Toggle control signals on an edge that doesn't correspond
        // to where the controls are sampled; in this example we do
        // this only on a negedge of clk, because we know
        // reset is not sampled there.
        if (!top->clk) {
            if (contextp->time() > 1 && contextp->time() < 10) {
                top->reset_l = !1;  // Assert reset
            } else {
                top->reset_l = !0;  // Deassert reset
            }
            // Assign some other inputs
            top->in_quad += 0x12;
        }
        */
        ////////////////////////////////////////////////////////////////////////

        // Evaluate model
        // (If you have multiple models being simulated in the same
        // timestep then instead of eval(), call eval_step() on each, then
        // eval_end_step() on each. See the manual.)
        // top->eval();

        /* ------------------------------------------------------------------------
        // Read outputs
        VL_PRINTF("[%" PRId64 "] clk=%x rstl=%x iquad=%" PRIx64 " -> oquad=%" PRIx64
                  " owide=%x_%08x_%08x\n",
                  contextp->time(), top->clk, top->reset_l, top->in_quad, top->out_quad,
                  top->out_wide[2], top->out_wide[1], top->out_wide[0]);
        */
    }

    // Final model cleanup
    top->final();

    // Coverage analysis (calling write only after the test is known to pass)
#if VM_COVERAGE
    Verilated::mkdir("logs");
    contextp->coveragep()->write("logs/coverage.dat");
#endif

    // Final simulation summary
    contextp->statsPrintSummary();

    // Return good completion status
    // Don't use exit() or destructor won't get called
    return 0;
}
