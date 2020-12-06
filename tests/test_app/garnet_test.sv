/*=============================================================================
** Module: garnet_test.sv
** Description:
**              program for garnet testbench
** Author: Keyi Zhang, Taeyoung Kong
** Change history:  10/14/2020 - Implement the first version
**===========================================================================*/
import "DPI-C" function int initialize_monitor(int num_cols);

program garnet_test #(
    parameter int MAX_NUM_APPS = 3
) (
    input logic clk, reset,
    proc_ifc p_ifc,
    axil_ifc axil_ifc
);
    //============================================================================//
    // local variables
    //============================================================================//
    Kernel kernels[];
    Environment env;

    initial begin
        initialize();
        map(kernels);

        env = new(kernels, axil_ifc, p_ifc);
        env.build();
        env.run();
    end

    //============================================================================//
    // initialize
    //============================================================================//
    function void initialize();
        int num_cols;
        int num_app;
        int result;
        string app_dirs[$], temp_str;

        num_cols = CGRA_WIDTH;
        result = initialize_monitor(num_cols);

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
            end
            else begin
                num_app = i;
                break;
            end
        end

        kernels = new[num_app];
        foreach (app_dirs[i]) begin
            kernels[i] = new(app_dirs[i]);
        end
    endfunction

    function void map(Kernel kernels[]);
        foreach(kernels[i]) begin
            if (kernels[i].kernel_map() == 0) begin
                $finish(2);
            end
        end
    endfunction
endprogram

