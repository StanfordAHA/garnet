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
    axil_ifc axil_ifc,
    output logic cgra_reset
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

        map(kernels);

        env = new(kernels, axil_ifc, p_ifc, dpr);
        env.build();

        test_toggle = 1;
        env.run();
        test_toggle = 0;

        // Dump out data between each test
        //env.compare();

    end

    initial begin
        // Wait until 'env' and 'env.proc_drv' are initialized
        wait (env != null && env.proc_drv != null);
        cgra_reset = env.proc_drv.cgra_reset;
        forever begin
            @(env.proc_drv.cgra_reset);
            cgra_reset = env.proc_drv.cgra_reset;
        end
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

        num_app = 0;
        for (int i = 0; i < MAX_NUM_APPS; i++) begin
            automatic string arg_name = {$sformatf("APP%0d", i), "=%s"};
            if ($value$plusargs(arg_name, temp_str)) begin
                // we have it
                app_dirs.push_back(temp_str);
            end else begin
                num_app = i;
                break;
            end
        end

        foreach (app_dirs[i]) begin
            temp_kernel = new(app_dirs[i], dpr);
            if (temp_kernel.num_glb_tiling > 0) begin
                // Replicate kernels if glb_tiling is enabled
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
                kernels.push_back(temp_kernel);
            end
        end
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

