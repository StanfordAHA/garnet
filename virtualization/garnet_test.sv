/*=============================================================================
** Module: garnet_test.sv
** Description:
**              program for garnet testbench
** Author: Keyi Zhang, Taeyoung Kong
** Change history:  10/14/2020 - Implement the first version
**===========================================================================*/

program garnet_test #(
    parameter int MAX_NUM_APPS = 3
) (
    input logic clk, reset, interrupt,
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

        env = new(kernels, axil_ifc, p_ifc, interrupt);
        env.build();
        env.load();
        env.run();
    end

    //============================================================================//
    // initialize
    //============================================================================//
    function void initialize();
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
            string app_name;
            string meta_name;
            string dir;
            string bs_location, input_location, gold_location;
            int last_str;
            dir = app_dirs[i];
            last_str = dir.getc(dir.len() - 1) == "/"? dir.len() - 2: dir.len() - 1;

            for (int i = dir.len() - 1; i >= 0; i--) begin
                if (dir.getc(i) == "/" && i != (dir.len() - 1)) begin
                    app_name = dir.substr(i + 1, last_str);
                    break;
                end
            end
            if (app_name.len() == 0) app_name = dir;
            meta_name = {dir, "/bin/", "design.meta"};
            kernels[i] = new(meta_name);
        end
    endfunction

    function void map(Kernel kernels[]);
        foreach(kernels[i]) begin
            if (kernels[i].kernel_map() == 0) begin
                $display("map error");
                $finish(2);
            end else begin
                $display("map success");
            end
        end
    endfunction
endprogram

