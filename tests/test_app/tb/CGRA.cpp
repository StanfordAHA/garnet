// DESCRIPTION: Verilator: Verilog example module
// See /usr/local/share/verilator/examples/make_tracing_c/sim_main.cpp
//======================================================================

// For std::unique_ptr
#include <memory>

// Include common routines
#include <verilated.h>

// Include model header, generated from Verilating "top.v"
#include "Vtop.h"

// Legacy function required only so linking works on Cygwin and MSVC++
double sc_time_stamp() { return 0; }

int main(int argc, char** argv) {

    // '5000' means 5ns. Why? Maybe b/c timescale = 1ps/1ps
    int ns = 1000;

    // Sets MAX_NS if ANY cmd-line arg is found to be an integer (I'm so clever haha)
    // E.g. "vtop 300" will run for 300ns and then end abruptly
    int MAX_NS = 300*ns;
    for (int i=1; i<argc; i++) {
        int maybe_integer = atoi(argv[i]);
        if (maybe_integer > 0) MAX_NS = maybe_integer;
    }
    // Create logs/ directory in case we have traces to put under it
    Verilated::mkdir("logs");

    // Construct a VerilatedContext to hold simulation time, etc.
    // Multiple modules (made later below with Vtop) may share the same
    // context to share time, or modules may have different contexts if
    // they should be independent from each other.

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
    contextp->randReset(0);  // 0: init to zero; 1: init to 1; 2: init to random

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
    top->reset_l = !0;
    top->clk = 0;
    top->in_small = 1;
    top->in_quad = 0x1234;
    top->in_wide[0] = 0x11111111;
    top->in_wide[1] = 0x22222222;
    top->in_wide[2] = 0x3;
    */

    // Simulate until $finish                                             <
    int i=-1;
    while (!contextp->gotFinish()) {
        i++; if (i > MAX_NS*ns) break;  // (Note "i" starts at -1)
        top->eval();
        contextp->timeInc(1);  // 1ps maybe
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
