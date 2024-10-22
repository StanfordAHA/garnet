// class Environment;
// function Environment::new(Kernel kernels[], vAxilIfcDriver vifc_axil, vProcIfcDriver vifc_proc, int dpr);
// function void Environment::build();

// TODO
// NOW: 'kernels[0]'
// WANT: 'kernel'

// task Environment::write_bs(Kernel kernel);
realtime start_time, end_time;
// Kernel Environment_write_bs_kernel;
Kernel kernel;

task Environment_write_bs();
    $timeformat(-9, 2, " ns", 0);
    repeat (10) @(p_ifc.clk);
    start_time = $realtime;
    $display("[%s] write bitstream to glb start at %0t", kernel.name, start_time);

    // proc_drv  = new(p_ifc, proc_lock);
    // proc_drv.write_bs(kernel.bs_start_addr, kernel.bitstream_data);

    ProcDriver_write_bs_start_addr = kernel.bs_start_addr;
    ProcDriver_write_bs_bs_q = kernel.bitstream_data;
    ProcDriver_write_bs();

    end_time = $realtime;
    $display("[%s] write bitstream to glb end at %0t", kernel.name, end_time);
    $display("[%s] It takes %0t time to write the bitstream to glb.",
             kernel.name, end_time - start_time);
endtask // Environment_write_bs

// task Environment::write_data(Kernel kernel);
// task Environment::read_data(Kernel kernel);
// task Environment::glb_configure(Kernel kernel);
// task Environment::cgra_configure(Kernel kernel);
// function bit [NUM_GLB_TILES-1:0] Environment::calculate_glb_stall_mask(int start, int num);
// function bit [NUM_CGRA_COLS-1:0] Environment::calculate_cgra_stall_mask(int start, int num);
// task Environment::cgra_stall(bit [NUM_CGRA_COLS-1:0] stall_mask);
// task Environment::cgra_unstall(bit [NUM_CGRA_COLS-1:0] stall_mask);
// task Environment::kernel_test(Kernel kernel);
// task Environment::wait_interrupt(e_glb_ctrl glb_ctrl, bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);
// task Environment::clear_interrupt(e_glb_ctrl glb_ctrl, bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);


// task Environment::set_interrupt_on();
task Environment_set_interrupt_on();
    $display("Turn on interrupt enable registers");
    addr = `GLC_GLOBAL_IER_R;      data = 3'b111; AxilDriver_write();
    addr = `GLC_PAR_CFG_G2F_IER_R; data =   1'b1; AxilDriver_write();
    addr = `GLC_STRM_F2G_IER_R;    data =   1'b1; AxilDriver_write();
    addr = `GLC_STRM_G2F_IER_R;    data =   1'b1; AxilDriver_write();
endtask


// task Environment::run();
// Short-handle aliases for AxilDriver_write_{addr,data}
bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
bit [CGRA_AXI_DATA_WIDTH-1:0] data;

task Environment_run();
    $display("environment L350: // wait for reset"); $fflush();  // 100ns
    repeat (20) @(posedge p_ifc.clk);
    $display("environment L352: waited 20 clocks"); $fflush();

    // turn on interrupt
    // set_interrupt_on();
    Environment_set_interrupt_on();

    // BOOKMARK
    // if (dpr) begin
    // assert dpr == 0
    foreach (kernels[i]) begin
        automatic int j = i;  // WHY???
        begin
            // write_bs(kernels[j]);
            kernel = kernels[j];
            Environment_write_bs();
        end
        $display("\n...guess what there was %0d kernels...\n", j);
    end
endtask



// task Environment::compare();
