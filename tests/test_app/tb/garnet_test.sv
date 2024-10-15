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

    //============================================================================//
    // local variables
    //============================================================================//
    Kernel kernels[$]; // use dynamic array for potential glb tiling
    Environment env;

    initial begin
        if ($value$plusargs("DPR=%d", value)) begin
            dpr = 1;
        end

        #100 initialize(dpr);

       $display("about to map"); $fflush();
        map(kernels);
       $display("done did map"); $fflush();

       $display("about to build"); $fflush();
        env = new(kernels, axil_ifc, p_ifc, dpr);
        env.build();
       $display("done did build"); $fflush();

        test_toggle = 1;
        env.run();
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
        $display("Looking for app args e.g. '+APP0=app0'"); $fflush();
        $display("Looking for app args e.g. '+APP0=app0'"); $fflush();
        num_app = 0;
        for (int i = 0; i < MAX_NUM_APPS; i++) begin
            automatic string arg_name = {$sformatf("APP%0d", i), "=%s"};
           $display("L80 i=%d", i); $fflush();
            if ($value$plusargs(arg_name, temp_str)) begin
               $display("L82 i=%d", i); $fflush();
                // we have it
                app_dirs.push_back(temp_str);
               $display("L85 i=%d", i); $fflush();
                $display("Found app '%s'", temp_str);

// ???
// Found app '/aha/garnet/SPARSE_TESTS/vec_elemadd_0/GLB_DIR/vec_elemadd_combined_seed_0'


            end else begin
               $display("L88 i=%d", i); $fflush();
                num_app = i;
                break;
            end
        end
       $display("L93"); $fflush();
        if (num_app == 0) begin
           $display("ERROR did not find app args"); $fflush();
           $finish(2);  // The only choices are 0,1,2; note $finish() is more drastic than $exit()
        end
       $display("L98"); $fflush();

       // SEG FAULT HERE
       // -bash: line 233: 1055010 Segmentation fault      (core dumped) Vtop "$APP" +trace

        foreach (app_dirs[i]) begin
           $display("processing app %d", i); $fflush();
           
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

