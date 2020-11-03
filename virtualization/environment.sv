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
    bit interrupt;

    Kernel kernels[];
    int num_app;

    ProcDriver proc_drv;
    AxilDriver axil_drv;

    extern function new(Kernel kernels[], vAxilIfcDriver vifc_axil, vProcIfcDriver vifc_proc, bit interrupt);
    extern function void build();
    extern task load();
    extern task configure();
    //extern task test();
    //extern task post_test();
    extern task run();
endclass

function Environment::new(Kernel kernels[], vAxilIfcDriver vifc_axil, vProcIfcDriver vifc_proc, bit interrupt);
    this.kernels = kernels;
    this.num_app = kernels.size();
    this.vifc_axil = vifc_axil;
    this.vifc_proc = vifc_proc;
    this.interrupt = interrupt;
endfunction

function void Environment::build();
    proc_drv = new(vifc_proc.driver);
    axil_drv = new(vifc_axil.driver);
endfunction

task Environment::load();
    // wait for reset
    repeat (20) @(vifc_proc.cbd);

    foreach(kernels[i]) begin
        proc_drv.write_bs(kernels[i].bs_start_addr, kernels[i].bitstream_data);
        foreach(kernels[i].input_data[j]) begin
            proc_drv.write_data(kernels[i].input_start_addr[j], kernels[i].input_data[j]);
        end
    end
endtask

task Environment::configure();
    foreach(kernels[i]) begin
        foreach(kernels[i].bs_cfg[j]) begin
            axil_drv.write(kernels[i].bs_cfg[j].addr, kernels[i].bs_cfg[j].data);
        end
        foreach(kernels[i].input_cfg[j]) begin
            foreach(kernels[i].input_cfg[j][k]) begin
                axil_drv.write(kernels[i].input_cfg[j][k].addr, kernels[i].input_cfg[j][k].data);
            end
        end
        foreach(kernels[i].output_cfg[j]) begin
            foreach(kernels[i].output_cfg[j][k]) begin
                axil_drv.write(kernels[i].output_cfg[j][k].addr, kernels[i].output_cfg[j][k].data);
            end
        end
        foreach(kernels[i].tile_cfg[j]) begin
            axil_drv.write(kernels[i].tile_cfg[j].addr, kernels[i].tile_cfg[j].data);
        end
    end
endtask

//task Environment::test();
//    int max_cycle;
//    fork : timeout_block
//        wait(scb.no_trans == kernels.size());
//        begin
//            max_cycle = 1_000_000;
//            $value$plusargs("MAX_CYCLE=%0d", max_cycle);
//            repeat (max_cycle) @(vifc_proc.cbd);
//            $display("@%0t: %m ERROR: Generator timeout ", $time);
//        end
//    join_any
//    disable fork;
//endtask

task Environment::run();
    configure();
    //test();
    //post_test();
endtask

//task Environment::post_test();
//    int max_cycle;
//    fork : timeout_block
//        wait(scb.no_trans == kernels.size());
//        begin
//            max_cycle = 1_000_000;
//            $value$plusargs("MAX_CYCLE=%0d", max_cycle);
//            repeat (max_cycle) @(vifc_proc.cbd);
//            $display("@%0t: %m ERROR: Generator timeout ", $time);
//        end
//    join_any
//    disable fork;
//endtask
