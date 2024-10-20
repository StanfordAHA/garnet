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
   bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
   
   bit [CGRA_AXI_DATA_WIDTH-1:0] data;
   


    //============================================================================//
    // local variables
    //============================================================================//
    Kernel kernels[$]; // use dynamic array for potential glb tiling
    // Environment env;

    initial begin
       axil_lock = new(1);
       
        if ($value$plusargs("DPR=%d", value)) begin
            dpr = 1;
        end

        #100 initialize(dpr);

       $display("about to map"); $fflush();
        map(kernels);
       $display("done did map"); $fflush();

       $display("about to build"); $fflush();
        // env = new(kernels, axil_ifc, p_ifc, dpr);

// THIS WORKS get a pulse at 101ns


    @(posedge axil_ifc.clk);                 // WAS CLOCKING @(vif.cbd)
    axil_ifc.wvalid = 1'b0;                // WAS CLOCKING vif.cbd<>
    @(posedge axil_ifc.clk);                 // WAS CLOCKING @(vif.cbd)
   $display("gtest 36: i see axil_ifc.wvalid = %0d (should be 0)", axil_ifc.wvalid); $fflush();

    axil_ifc.wvalid = 1'b1;                // WAS CLOCKING axil_ifc.cbd<>
    @(posedge axil_ifc.clk);                 // WAS CLOCKING @(axil_ifc.cbd)
   $display("gtest 39: i see axil_ifc.wvalid = %0d (should be 1)", axil_ifc.wvalid); $fflush();

    axil_ifc.wvalid = 1'b0;                // WAS CLOCKING axil_ifc.cbd<>
    @(posedge axil_ifc.clk);                 // WAS CLOCKING @(axil_ifc.cbd)
   $display("gtest 44: i see axil_ifc.wvalid = %0d (should be 0)", axil_ifc.wvalid); $fflush();

//    semaphore proc_lock;
//    semaphore axil_lock;
//    vAxilIfcDriver vifc_axil;
//    vProcIfcDriver vifc_proc;
//        env.build();

//    proc_lock = new(1);
//    axil_lock = new(1);
//    proc_drv  = new(vifc_proc, proc_lock);
//    axil_drv  = new(vifc_axil, axil_lock);



       $display("done did build"); $fflush();  // happens at 103ns


// THIS WORKS get a pulse at 105.5ns

    @(posedge axil_ifc.clk);                 // WAS CLOCKING @(vif.cbd)
    axil_ifc.wvalid = 1'b0;                // WAS CLOCKING vif.cbd<>
    @(posedge axil_ifc.clk);                 // WAS CLOCKING @(vif.cbd)
   $display("gtest 36a: i see axil_ifc.wvalid = %0d (should be 0)", axil_ifc.wvalid); $fflush();

    axil_ifc.wvalid = 1'b1;                // WAS CLOCKING axil_ifc.cbd<>
    @(posedge axil_ifc.clk);                 // WAS CLOCKING @(axil_ifc.cbd)
   $display("gtest 39a: i see axil_ifc.wvalid = %0d (should be 1)", axil_ifc.wvalid); $fflush();

    // this happens at around 107ns
    axil_ifc.wvalid = 1'b0;                // WAS CLOCKING axil_ifc.cbd<>
    @(posedge axil_ifc.clk);                 // WAS CLOCKING @(axil_ifc.cbd)
   $display("gtest 44a: i see axil_ifc.wvalid = %0d (should be 0)", axil_ifc.wvalid); $fflush();











        test_toggle = 1;



       // env.run();


    $display("environment L350: // wait for reset"); $fflush();
       // repeat (20) @(posedge vifc_proc.clk);
    repeat (20) @(posedge p_ifc.clk);
    // 127ns
    $display("environment L352: waited 20 clocks"); $fflush();


//    AxilDriver axil_drv;



   // 128ns maybe
   $display("FOO time [%t]", $time);
    $display("axil_driver 36: i see vif.wvalid = %0d (should be 0)", axil_ifc.wvalid); $fflush();
    axil_ifc.wvalid = 1'b1;                // WAS CLOCKING vif.cbd<>
    // vif.driver.wvalid = 1'b1;  // MemberSel of non-variable
    @(posedge axil_ifc.clk);                 // WAS CLOCKING @(vif.cbd)
    $display("axil_driver 39: i see vif.wvalid = %0d (should be 1)", axil_ifc.wvalid); $fflush();
    repeat (20) @(posedge axil_ifc.clk);
    @(posedge axil_ifc.clk);                 // WAS CLOCKING @(vif.cbd)
    axil_ifc.wvalid = 1'b0;                // WAS CLOCKING vif.cbd<>


// ==============================================================================
// ==============================================================================
// ==============================================================================
// semaphore axil_lock;
// bit [CGRA_AXI_ADDR_WIDTH-1:0] addr, 
// bit [CGRA_AXI_DATA_WIDTH-1:0] data);


//       // set_interrupt_on();
    $display("Turn on interrupt enable registers");
//    axil_ifc.write(`GLC_GLOBAL_IER_R, 3'b111);


       addr = `GLC_GLOBAL_IER_R;
       data = 3'b111;

    // $display("AXI-Lite Write. Addr: %08h, Data: %08h", addr, data);
    $display("AXI-Lite Write. Addr: %08h, Data: %08h", addr, data);
    $display("axil_driver: Gettum lockum"); $fflush();
    axil_lock.get(1);
    $display("axil_driver: Gottum lockum"); $fflush();



    $display("axil_driver 32: i see axil_ifc.wvalid = %0d", axil_ifc.wvalid); $fflush();

    @(posedge axil_ifc.clk);                 // WAS CLOCKING @(vif.cbd)
    axil_ifc.awaddr  = addr;                // WAS CLOCKING vif.cbd.<>
    axil_ifc.awvalid = 1'b1;                // WAS CLOCKING vif.cbd<>
    for (int i = 0; i < 100; i++) begin
        if (axil_ifc.awready == 1) break;    // WAS CLOCKING vif.cbd<>
        @(posedge axil_ifc.clk);             // WAS CLOCKING @(vif.cbd)
        // if (i == 99) return;  // axi slave is not ready
    end

    $finish(0);






        test_toggle = 0;

        // Dump out data between each test
        //env.compare();
       $display("done did all of garnet_test i guess"); $fflush();
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
endprogram

