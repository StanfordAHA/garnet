/*=============================================================================
** Module: garnet_test.sv
** Description:
**              program for garnet testbench
** Author: Keyi Zhang, Taeyoung Kong
** Change history:  10/14/2020 - Implement the first version
**===========================================================================*/
program garnet_test #(
    parameter int MAX_NUM_APPS = 2
) (
    input logic clk, reset, interrupt,
    proc_ifc p_ifc,
    axil_ifc axil_ifc
);
    //============================================================================//
    // local variables
    //============================================================================//
    Kernel kernels[];
    // Environment env;

    initial begin
        initialize();
        env = new(kernels, p_vif, r_vif, interrupt);
        env.build();
        env.run();
    end

    //============================================================================//
    // initialize
    //============================================================================//
    task initialize;
        bitstream_t bitstream;
        data_array_t input_data;
        data_array_t gold_data;
        int num_app;
        string app_dirs[$], temp_str;
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
            // get app name
            automatic string app_name;
            automatic string dir;
            automatic string bs_location, input_location, gold_location;
            automatic int last_str;
            dir = app_dirs[i];
            last_str = dir.getc(dir.len() - 1) == "/"? dir.len() - 2: dir.len() - 1;

            for (int i = dir.len() - 1; i >= 0; i--) begin
                if (dir.getc(i) == "/" && i != (dir.len() - 1)) begin
                    app_name = dir.substr(i + 1, last_str);
                    break;
                end
            end
            if (app_name.len() == 0) app_name = dir;
            bs_location = {dir, "/bin/", app_name, ".bs"};
            input_location = {dir, "/bin/", "input.raw"};
            gold_location = {dir, "/bin/", "gold.raw"};
            bitstream = IOHelper::get_bitstream(bs_location);
            input_data = IOHelper::get_input_data(input_location);
            gold_data  = IOHelper::get_gold_data(gold_location);
            kernels[i] = new(i, bitstream, input_data, gold_data);
        end
    endtask
endprogram

