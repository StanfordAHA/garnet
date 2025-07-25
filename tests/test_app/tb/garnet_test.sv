/*=============================================================================
** Module: garnet_test.sv
** Description:
**              program for garnet testbench
** Author: Keyi Zhang, Taeyoung Kong
** Change history:  10/14/2020 - Implement the first version
**===========================================================================*/
import "DPI-C" function int initialize_monitor(int num_cols);

// UNUSED methinks but verilator dies when it can't be found ("undefined reference")
// import "DPI-C" function int get_external_mu_active_arr_env_var();

program garnet_test #(
    parameter int MAX_NUM_APPS = 1000
) (
    input logic clk,
    reset,
    proc_ifc p_ifc,
    axil_ifc axil_ifc,
    axil_ifc mu_axil_ifc,
    behavioral_matrix_unit behavioral_mu_ifc
);
    int test_toggle = 0;
    int value;
    int dpr = 0;

    //============================================================================//
    // local variables
    //============================================================================//
    Kernel kernels[$]; // use dynamic array for potential glb tiling
    int external_mu_active_arr[$]; // use dynamic array for potential glb tiling
    DnnLayer dnn_layers[$]; // use dynamic array for potential glb tiling

    // Incorrect timescale gave me no end of problems, so now I'm adding this to help future me.
    function static void time_check(bit cond);
        automatic string ex1 = "vcs '--timescale=1ps/1ps'";
        automatic string ex2 = "verilator '--timescale 1ps/1ps'";
        if (!cond)
          $fatal(13, {$sformatf("\nINCORRECT TIMESCALE: use %s or %s\n\n", ex1, ex2)});
    endfunction // time_check

    // Time check. For test to PASS, must have timescale == 1ps/1ps
    //   First  check succeeds iff timeunit == 1ps
    //   Second check succeeds iff timeprecision == 1ps
    int irt; real rrt;
    initial begin
        #1;  // Advance one timestep
        irt = real'(int'($realtime)); rrt = real'($realtime);
        // TESTING               // 1ps/1ps 1ps/1fs 1ns/1ps 1ns/1ns
        time_check(1ps == 1.0);  //   pass    pass   ERROR   ERROR
        time_check(irt == rrt);  //   pass    ERROR
    end

    initial begin
        if ($value$plusargs("DPR=%d", value)) begin
            dpr = 1;
        end

        #100 initialize(dpr);  // So...I guess this is supposed to happen at 100ps not 100ns...

        map(kernels);

        test_toggle = 1;
        Env_run();
        test_toggle = 0;

        // Dump out data between each test
        //env.compare();

        $display("Time: %0t", $time);
        $display("PASS PASS PASS PASS PASS PASS PASS PASS PASS PASS\n");
        $finish(0);
    end

    //============================================================================//
    // initialize
    //============================================================================//
    function static void initialize(int dpr);
        int num_cols;
        int num_app;
        int result;
        string app_dirs[$], temp_str;
        string mu_app_dirs[$];
        Kernel temp_kernel, kernel;
        DnnLayer tmp_dnn_layer;
        int kernel_glb_tiling_cnt = 0;

        num_cols = NUM_CGRA_COLS;
        result   = initialize_monitor(num_cols);

        if (result == 1) begin
            $display("Monitor initialization success");
        end else begin
            $display("Monitor initialization failed");
        end

        $display("Looking for app args e.g. '+APP0=app0'");
        num_app = 0;
        for (int i = 0; i < MAX_NUM_APPS; i++) begin
            automatic string arg_name = {$sformatf("APP%0d", i), "=%s"};
            automatic string mu_arg_name;
            if ($value$plusargs(arg_name, temp_str)) begin
                // we have it
                app_dirs.push_back(temp_str);
                $display("Found app '%s'", temp_str);

                // MU test can be specified as a real test or as "inactive"
                // Or if not specified, MU is assumed inactive
                mu_arg_name = {$sformatf("MU_TEST%0d", i), "=%s"};
                if ($value$plusargs(mu_arg_name, temp_str)) begin
                    if (temp_str != "inactive") begin
                         // we have it and it is active
                        $display("Found MU test '%s'", temp_str);
                        mu_app_dirs.push_back(temp_str);
                        external_mu_active_arr.push_back(1);
                        $display("External MU active for app %0d", i);
                    end else begin
                        mu_app_dirs.push_back("");
                        external_mu_active_arr.push_back(0);
                        $display("External MU inactive for app %0d", i);
                    end
                end else begin
                    // no mu test
                    mu_app_dirs.push_back("");
                    external_mu_active_arr.push_back(0);
                    $display("External MU inactive for app %0d", i);
                end

            end else begin
                num_app = i;
                break;
            end
        end
        if (num_app == 0) begin
           $display("ERROR did not find app args");
           $finish(2);  // The only choices are 0,1,2; note $finish() is more drastic than $exit()
        end

        foreach (app_dirs[i]) begin
            $display("[%0t] Processing app #%0d\n", $time, i);
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

        foreach (mu_app_dirs[i]) begin
            tmp_dnn_layer = new();
            if (mu_app_dirs[i] != "") begin
                tmp_dnn_layer.read_params(mu_app_dirs[i]);
            end
            dnn_layers.push_back(tmp_dnn_layer);
        end

        $display("End function 'initialize'\n");
    endfunction

    function void map(Kernel kernels[]);
        foreach (kernels[i]) begin
            $display("\n[%0t] Start mapping kernel %0d", $time, i);
            if (kernels[i].kernel_map() == 0) begin
                $display("Mapping kernel %0d Failed", i);
                $finish(2);
            end
            $display("[%0t] Mapping kernel %0d Succeed\n", $time, i);
        end
    endfunction

   `include "tb/environment.sv"
endprogram
