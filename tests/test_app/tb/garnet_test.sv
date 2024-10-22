/*=============================================================================
** Module: garnet_test.sv
** Description:
**              program for garnet testbench
** Author: Keyi Zhang, Taeyoung Kong
** Change history:  10/14/2020 - Implement the first version
**===========================================================================*/
import "DPI-C" function int initialize_monitor(int num_cols);
program garnet_test #(
    parameter int MAX_NUM_APPS = 1000
) (
    input logic clk,
    reset,
    proc_ifc p_ifc,
    axil_ifc axil_ifc
);
    int test_toggle = 0;
    int value;
    int dpr = 0;

    semaphore axil_lock;
    semaphore proc_lock;

    bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
    bit [CGRA_AXI_DATA_WIDTH-1:0] data;

    //  task Environment::write_bs(Kernel kernel);
    realtime start_time, end_time;
    ProcDriver proc_drv;
   
    //============================================================================//
    // local variables
    //============================================================================//
    Kernel kernels[$]; // use dynamic array for potential glb tiling
    // Environment env;

    initial begin
       axil_lock = new(1);
       proc_lock = new(1);

       
        if ($value$plusargs("DPR=%d", value)) begin
            dpr = 1;
        end

        #100 initialize(dpr);

        $display("mapping..."); $fflush();
        map(kernels);
        // $display("mapped."); $fflush();

        // No longer need "build()" b/c now using tasks instead of classes
        // env = new(kernels, axil_ifc, p_ifc, dpr);
        // env.build();

        test_toggle = 1;
        env_run();  // Task must have no args, else cannot see signals in gtkwave (???)
        test_toggle = 0;

        // Dump out data between each test
        //env.compare();
       $display("done did all of garnet_test i guess"); $fflush();
       $finish(0);
    end

    //============================================================================//
    // initialize
    //============================================================================//
    function void initialize(int dpr);
        int num_cols;
        int num_app;
        int result;
        string app_dirs[$], temp_str;
        Kernel temp_kernel, kernel;
        int kernel_glb_tiling_cnt = 0;

        num_cols = NUM_CGRA_COLS;
        result   = initialize_monitor(num_cols);

        if (result == 1) begin
            $display("Monitor initialization success");
        end else begin
            $display("Monitor initialization failed");
        end

        // Looking for...? Something like...?
        // +APP0=app0
       $display("[%0t] garnet_test L75\n", $time);
        $display("Looking for app args e.g. '+APP0=app0'"); $fflush();
        num_app = 0;
        for (int i = 0; i < MAX_NUM_APPS; i++) begin
            automatic string arg_name = {$sformatf("APP%0d", i), "=%s"};
            if ($value$plusargs(arg_name, temp_str)) begin
                // we have it
                app_dirs.push_back(temp_str);
                $display("Found app '%s'", temp_str);
            end else begin
                num_app = i;
                break;
            end
        end
        if (num_app == 0) begin
           $display("ERROR did not find app args"); $fflush();
           $finish(2);  // The only choices are 0,1,2; note $finish() is more drastic than $exit()
        end

       // SEG FAULT HERE
       // -bash: line 233: 1055010 Segmentation fault      (core dumped) Vtop "$APP" +trace

        foreach (app_dirs[i]) begin
           $display("processing app #%0d", i); $fflush();
           
            temp_kernel = new(app_dirs[i], dpr);
            if (temp_kernel.num_glb_tiling > 0) begin
                // Replicate kernels if glb_tiling is enabled
      $display("// Replicate kernels if glb_tiling is enabled"); $fflush();
                temp_kernel.glb_tiling_cnt = kernel_glb_tiling_cnt;
                kernel_glb_tiling_cnt++;
                kernels.push_back(temp_kernel);
                repeat (temp_kernel.num_glb_tiling - 1) begin
                    kernel = new(app_dirs[i], dpr);
                    kernel.glb_tiling_cnt = kernel_glb_tiling_cnt;
                    kernel_glb_tiling_cnt++;
                    kernels.push_back(kernel);
                end
                kernel_glb_tiling_cnt = 0;
            end else begin
                // No glb tiling
      $display("// No glb tiling"); $fflush();
                kernels.push_back(temp_kernel);
            end
        end
        $display("End function 'initialize'"); $fflush();
    endfunction

    function void map(Kernel kernels[]);
        foreach (kernels[i]) begin
            $display("\nStart mapping kernel %0d", i);
            if (kernels[i].kernel_map() == 0) begin
                $display("Mapping kernel %0d Failed", i);
                $finish(2);
            end
            $display("Mapping kernel %0d Succeed", i);
        end
    endfunction

   // TODO this should be separate 'include' file, like task_axil_drive below...
   task env_run();

      // task Environment::run();
      // repeat (20) @(posedge vifc_proc.clk);

      $display("environment L350: // wait for reset"); $fflush();  // 100ns
      repeat (20) @(posedge p_ifc.clk);
      $display("environment L352: waited 20 clocks"); $fflush();

      // turn on interrupt
      // set_interrupt_on();

      // task Environment::set_interrupt_on();
      $display("Turn on interrupt enable registers");

      // axil_drv.write(`GLC_GLOBAL_IER_R, 3'b111);
      // axil_drv.write(`GLC_PAR_CFG_G2F_IER_R, {NUM_GLB_TILES{1'b1}});
      // axil_drv.write(`GLC_STRM_F2G_IER_R, {NUM_GLB_TILES{1'b1}});
      // axil_drv.write(`GLC_STRM_G2F_IER_R, {NUM_GLB_TILES{1'b1}});
      // endtask (set_interrupt_on)

      addr = `GLC_GLOBAL_IER_R;      data = 3'b111; axil_drive_write();
      addr = `GLC_PAR_CFG_G2F_IER_R; data =   1'b1; axil_drive_write();
      addr = `GLC_STRM_F2G_IER_R;    data =   1'b1; axil_drive_write();
      addr = `GLC_STRM_G2F_IER_R;    data =   1'b1; axil_drive_write();

// BOOKMARK what comes after set_interrupt_on?

    // if (dpr) begin
    //     foreach (kernels[i]) begin
    //         automatic int j = i;
    //         fork
    //             begin
    //                 write_bs(kernels[j]);


// TODO NEXT this should be a task e.g. 'env_write_bs'
    //  // Want to do one of these where kernel=kernel[0]
    //  task Environment::write_bs(Kernel kernel);
    //      realtime start_time, end_time;
    //      $timeformat(-9, 2, " ns");
    //      repeat (10) @(vifc_proc.cbd);
    //      start_time = $realtime;
    //      $display("[%s] write bitstream to glb start at %0t", kernel.name, start_time);
    //      proc_drv.write_bs(kernel.bs_start_addr, kernel.bitstream_data);
    //      end_time = $realtime;
    //      $display("[%s] write bitstream to glb end at %0t", kernel.name, end_time);
    //      $display("[%s] It takes %0t time to write the bitstream to glb.", kernel.name,
    //               end_time - start_time);
    //  endtask

    $timeformat(-9, 2, " ns", 0);
    // repeat (10) @(vifc_proc.cbd);
    repeat (10) @(p_ifc.clk);
    start_time = $realtime;
    $display("[%s] write bitstream to glb start at %0t", kernels[0].name, start_time);

    // TODO NEXT replace these with proc_drive_write_bs (see axil_drive_write above)
    proc_drv  = new(p_ifc, proc_lock);
    proc_drv.write_bs(kernels[0].bs_start_addr, kernels[0].bitstream_data);

    end_time = $realtime;
    $display("[%s] write bitstream to glb end at %0t", kernels[0].name, end_time);
    $display("[%s] It takes %0t time to write the bitstream to glb.", kernels[0].name,
             end_time - start_time);



   endtask

   `include "tb/task_axil_drive.sv"
endprogram

