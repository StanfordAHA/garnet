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

// TBD
// task Environment::write_data(Kernel kernel);
// task Environment::read_data(Kernel kernel);

// task Environment::glb_configure(Kernel kernel);
task Environment_glb_configure();
    $timeformat(-9, 2, " ns", 0);
    start_time = $realtime;
    $display("[%s] glb configuration start at %0t", kernel.name, start_time);

    // axil_drv.config_write(kernel.bs_cfg);
    // axil_drv.config_write(kernel.kernel_cfg);
    AxilDriver_cfg = kernel.bs_cfg;     AxilDriver_config_write();
    AxilDriver_cfg = kernel.kernel_cfg; AxilDriver_config_write();

    end_time = $realtime;
    $display("[%s] glb configuration end at %0t", kernel.name, end_time);
endtask

// TBD
// task Environment::cgra_configure(Kernel kernel);

Config Environment_cgra_configure_cfg;
int group_start, num_groups;
bit [NUM_GLB_TILES-1:0] glb_stall_mask;
bit [NUM_CGRA_COLS-1:0] cgra_stall_mask;

task Environment_cgra_configure();
    $timeformat(-9, 2, " ns", 0);
    group_start = kernel.group_start;
    num_groups = kernel.num_groups;
    // BOOKMARK
    // glb_stall_mask = calculate_glb_stall_mask(group_start, num_groups); // unused???
    Environment_cgra_stall_mask = calculate_cgra_stall_mask(group_start, num_groups);

    // cgra_stall(cgra_stall_mask);
    Environment_cgra_stall();
    start_time = $realtime;
    $display("[%s] fast configuration start at %0t", kernel.name, start_time);
    Environment_cgra_configure_cfg = kernel.get_pcfg_start_config();
    // axil_drv.write(cfg.addr, cfg.data);
    addr = Environment_cgra_configure_cfg.addr;
    data = Environment_cgra_configure_cfg.data;
    AxilDriver_write();

    // wait_interrupt(GLB_PCFG_CTRL, kernel.bs_tile);
    glb_ctrl = GLB_PCFG_CTRL;
    tile_num   = kernel.bs_tile;
    Environment_wait_interrupt();

    // clear_interrupt(GLB_PCFG_CTRL, kernel.bs_tile);
    glb_ctrl = GLB_PCFG_CTRL;
    tile_num   = kernel.bs_tile;
    Environment_clear_interrupt();

    end_time = $realtime;
    $display("[%s] fast configuration end at %0t", kernel.name, end_time);
    $display("[%s] It takes %0t time to do parallel configuration.", kernel.name,
             end_time - start_time);
endtask

// function bit [NUM_GLB_TILES-1:0] Environment::calculate_glb_stall_mask(int start, int num);
function bit [NUM_GLB_TILES-1:0] calculate_glb_stall_mask(int start, int num);
    calculate_glb_stall_mask = '0;
    for (int i = 0; i < num; i++) begin
        calculate_glb_stall_mask |= ((2'b11) << ((start + i) * 2));
    end
endfunction

// function bit [NUM_CGRA_COLS-1:0] Environment::calculate_cgra_stall_mask(int start, int num);
function bit [NUM_CGRA_COLS-1:0] calculate_cgra_stall_mask(int start, int num);
    calculate_cgra_stall_mask = '0;
    for (int i = 0; i < num; i++) begin
        calculate_cgra_stall_mask |= ((4'b1111) << ((start + i) * 4));
    end
endfunction

// task Environment::cgra_stall(bit [NUM_CGRA_COLS-1:0] stall_mask);
bit [CGRA_AXI_DATA_WIDTH-1:0] Environment_cgra_stall_data;
bit [CGRA_AXI_DATA_WIDTH-1:0] Environment_cgra_stall_wr_data;
bit [NUM_CGRA_COLS-1:0] Environment_cgra_stall_mask;
task Environment_cgra_stall();
    // AxilDriver_read(`GLC_CGRA_STALL_R, Environment_cgra_stall_data);  // TBD
    AxilDriver_read_addr = `GLC_CGRA_STALL_R;
    AxilDriver_read_data = Environment_cgra_stall_data;
    AxilDriver_read();

    Environment_cgra_stall_wr_data = Environment_cgra_stall_mask |
                                     Environment_cgra_stall_data;
    // AxilDriver_write(`GLC_CGRA_STALL_R, Environment_cgra_stall_wr_data);
    addr = `GLC_CGRA_STALL_R;
    data = Environment_cgra_stall_wr_data;
    AxilDriver_write();
    


    $display("Stall CGRA with stall mask %8h", Environment_cgra_stall_mask);
endtask

// TBD
// task Environment::cgra_unstall(bit [NUM_CGRA_COLS-1:0] stall_mask);
// task Environment::kernel_test(Kernel kernel);


// task Environment::wait_interrupt(e_glb_ctrl glb_ctrl,
//                                  bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);
typedef enum int {
    GLB_PCFG_CTRL,
    GLB_STRM_G2F_CTRL,
    GLB_STRM_F2G_CTRL
} e_glb_ctrl;
e_glb_ctrl glb_ctrl;

bit [$clog2(NUM_GLB_TILES)-1:0] tile_num;
string reg_name;
// bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
// bit [CGRA_AXI_DATA_WIDTH-1:0] data;
task Environment_wait_interrupt();
    // which interrupt
    if (glb_ctrl == GLB_PCFG_CTRL) begin
        addr = `GLC_PAR_CFG_G2F_ISR_R;
        reg_name = "PCFG";
    end else if (glb_ctrl == GLB_STRM_G2F_CTRL) begin
        addr = `GLC_STRM_G2F_ISR_R;
        reg_name = "STRM_G2F";
    end else begin
        addr = `GLC_STRM_F2G_ISR_R;
        reg_name = "STRM_F2G";
    end

    // So...this does what?
    // Starts two parallel threads?
    // When/if first thread gets and interrupt, we return?
    // ANd ALSO if no interrupt (or finish) after 6M cycles, we error and die?
    // Maybe...'join_any' means fork is complete when/if any subthread finishes??
    fork
        begin
            forever begin
                // level sensitive interrupt
                wait (top.interrupt);
                AxilDriver_read_addr = addr;
                AxilDriver_read_data = data;
                AxilDriver_read();
                if (data[tile_num] == 1) begin
                    $display("%s interrupt from tile %0d", reg_name, tile_num);
                    break;
                end
            end
        end
        begin
            /*
            // So...this runs forever I guess? and stops things if they run too long...?
            // If things work correctly...? Someone else pulls $finish before this hits error condition?
            repeat (5_000_000) @(posedge axil_ifc.clk);
            repeat (1_000_000) @(posedge axil_ifc.clk);
            $error("@%0t: %m ERROR: Interrupt wait timeout ", $time);
            $finish;
            */
            // copilot gave me this one
            forever begin
                @(posedge axil_ifc.clk);
                if ($time > 6_000_000) begin
                    $error("@%0t: %m ERROR: Interrupt wait timeout ", $time);
                    $finish;
                end
            end
            
        end
    join_any
    disable fork;
endtask


// clear_interrupt(GLB_PCFG_CTRL, kernel.bs_tile); // TBD
// glb_ctrl = GLB_PCFG_CTRL;
// tile_num   = kernel.bs_tile;
// Environment_clear_interrupt();

// task Environment::clear_interrupt(e_glb_ctrl glb_ctrl, bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);
// bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
// string reg_name;
bit [NUM_GLB_TILES-1:0] tile_mask;
task Environment_clear_interrupt();
    tile_mask = (1 << tile_num);

    // which interrupt
    if (glb_ctrl == GLB_PCFG_CTRL) begin
        addr = `GLC_PAR_CFG_G2F_ISR_R;
        reg_name = "PCFG";
    end else if (glb_ctrl == GLB_STRM_G2F_CTRL) begin
        addr = `GLC_STRM_G2F_ISR_R;
        reg_name = "STRM_G2F";
    end else begin
        addr = `GLC_STRM_F2G_ISR_R;
        reg_name = "STRM_F2G";
    end

    $display("%s interrupt clear", reg_name);
    // AxilDriver_write(addr, tile_mask);
    // addr = addr
    data = tile_mask;
    AxilDriver_write();
endtask


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
    // assert dpr == 0  TODO
    foreach (kernels[i]) begin
        automatic int j = i;  // WHY???
        begin
            // write_bs(kernels[j]);
            kernel = kernels[j];
            Environment_write_bs();

            // glb_configure(kernels[j]);
            Environment_glb_configure();

            // TODO
            // cgra_configure(kernels[j]);
            // write_data(kernels[j]);
            // kernel_test(kernels[j]);
            // read_data(kernels[j]);
            // kernels[j].compare();

            

        end
        $display("\n...guess what there was %0d kernels...\n", j);
    end
endtask



// task Environment::compare();
