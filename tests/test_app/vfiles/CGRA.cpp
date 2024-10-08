// #define VTOP Vtop Vtop_CGRA
// #include "Vtop_CGRA.h"

#define VTOP Vtop
#include "Vtop.h"

#include "verilated.h"
// #include "verilated_vcd_c.h"

// clock.vp had this:
//;    (Name=>'CLK_PERIOD', Val=>5000, Min=>2, Step=>2,
//;    (Name=>'RST_PERIOD', Val=>1, Min=>1, Step=>1,
//;    (Name=>'MAX_CYCLES', Val=>10, Min=>1, Step=>1,

#define CLK_PERIOD 5000
#define RST_PERIOD 1

// #define MAX_CYCLES 10
// ../tst/top_fftram.vp://; my $ncy = fftgen::log2($npoints) * ($npoints/2)/$nunits;
// ../tst/top_fftram.vp://;     MAX_CYCLES=>  ($ncy+6)  # End simulation after complete cycle plus some.

#define MAX_CYCLES 1000000 // "done" signal should stop us long before!


// Called by $time in Verilog. "double" matches SystemC (do i even care?)
double main_time;
double sc_time_stamp () { return main_time; }

  int main(int argc, char **argv, char **env) {
    int i;
    int clk;
    int ncy;
    Verilated::commandArgs(argc, argv);
    // init top verilog instance
    // Vtop_CGRA* top = new Vtop_CGRA;
    Vtop* top = new Vtop;
    // init trace dump
    //   Verilated::traceEverOn(true);
    //   VerilatedVcdC* tfp = new VerilatedVcdC;
    // top->trace (tfp, 99);
    //   tfp->open ("counter.vcd");

    //Uncomment to debug "didn't converge" error (see verilator manual "verilator --help")
    //Verilated::debug(1);

    top->eval(); // establish initial values?
    exit(0);
}







//     top->clk = 0;
//     top->eval(); // establish initial values?
//     ncy=0;
// 
//     // run simulation for 100 clock periods [20?]
//     //  for (i=0; i<20; i++) {
//     for (i=0; i<MAX_CYCLES; i++) {
// 
//         // First half cycle
//         clk = 0;
//         top->clk = 0;
// 
//         // top_CGRA should do this
//         //       //      if (i == (RST_PERIOD)) {
//         //       if (i == 1) {
//         //           // $display("\nRESET!!!\n");
//         //           if (top->rst_n == 1) printf("\nRESET!!!\n");
//         //           top->rst_n = 0; // Wait 10 cy before pulling reset low (active)
//         //       }
// 
//         // printf("------------------------------------------------------------------------------\n");
//         // printf("clock.vp: reset=%d, ncy=%3d, time=%6d ns\n", top->rst_n, i, i);
//         // printf("------------------------------------------------------------------------------\n");
// 
//         main_time = 500 * (2*i + clk); // Update the global clock for $time, I guess: 0, 500, 1000, ...
//         top->eval();
//         //tfp->dump(ncy+=5);
// 
//         // Second half cycle
//         clk = 1;
//         top->clk = 1;
//         main_time = 500 * (2*i + clk); // Update the global clock for $time, I guess: 0, 500, 1000, ...
//         top->eval();
//         //tfp->dump(ncy+=5);
// 
//         if (Verilated::gotFinish())  exit(0);
//         if (top->done == 1) break;
//     }
//     tfp->close();
//     exit(0);
// }
