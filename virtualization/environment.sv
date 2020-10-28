/*=============================================================================
** Module: environemnet.sv
** Description:
**              program to drive garnet testbench
** Author: Keyi Zhang, Taeyoung Kong
** Change history:  10/25/2020 - Implement the first version
**===========================================================================*/
class Environment;
    vAxilIfcDriver vifc_axil;
    vProcIfcDriver vifc_proc;
    GarnetMonitor mon;

    Kernel kernels[];

    event ker2env[];
    int num_app;

    extern function new(Kernel kernels[], vAxilIfcDriver vifc_axil, vProcIfcDriver vifc_proc, bit interrupt);
    extern task run();
    extern task build();
    extern task test();
    extern task post_test();
endclass

function Environment::new(Kernel kernels[], vAxilIfcDriver vifc_axil, vProcIfcDriver vifc_proc, bit interrupt);
    this.kernels = kernels;
    this.num_app = kernels.size();
    this.vifc_axil = vifc_axil;
    this.vifc_proc = vifc_proc;
endfunction

task Environment::build();
    mon = new();
endtask

task Environment::test();
    foreach(kernels[i]) begin
        fork
            int j = i;
            k_drv[j].run();
        join_none
    end

endtask

task Environment::post_test();
    int max_cycle;
    fork : timeout_block
        wait(scb.no_trans == kernels.size());
        begin
            max_cycle = 1_000_000;
            $value$plusargs("MAX_CYCLE=%0d", max_cycle);
            repeat (max_cycle) @(vifc_proc.cbd);
            $display("@%0t: %m ERROR: Generator timeout ", $time);
        end
    join_any
    disable fork;
endtask

task Environment::run();
    schedule();
    test();
    post_test();
endtask

