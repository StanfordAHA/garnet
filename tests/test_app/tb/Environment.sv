// class Environment;
// function Environment::new(Kernel kernels[], vAxilIfcDriver vifc_axil, vProcIfcDriver vifc_proc, int dpr);
// function void Environment::build();

// TODO
// NOW: 'kernels[0]'
// WANT: 'kernel'

realtime start_time, end_time, g2f_end_time, latency;
Kernel kernel;

bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
bit [CGRA_AXI_DATA_WIDTH-1:0] data;

bit [NUM_GLB_TILES-1:0] Env_glb_stall_mask;
bit [NUM_CGRA_COLS-1:0] Env_cgra_stall_mask;

typedef enum int {
    GLB_PCFG_CTRL,
    GLB_STRM_G2F_CTRL,
    GLB_STRM_F2G_CTRL
} e_glb_ctrl;
e_glb_ctrl glb_ctrl;

bit [$clog2(NUM_GLB_TILES)-1:0] tile_num;

`include "tb/ProcDriver.sv"
`include "tb/AxilDriver.sv"

// task Environment::write_bs(Kernel kernel);
task Env_write_bs();
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
endtask // Env_write_bs

// TBD
// task Environment::write_data(Kernel kernel);
task Env_write_data();
    realtime start_time, end_time;
    $timeformat(-9, 2, " ns", 0);

    repeat (10) @(posedge p_ifc.clk);
    foreach (kernel.inputs[i]) begin
        foreach (kernel.inputs[i].io_tiles[j]) begin
            if (kernel.inputs[i].io_tiles[j].is_glb_input == 1) begin
                // Skip writing input data that is already in GLB
                continue;
            end
            start_time = $realtime;
            $display("[%s] write input_%0d_block_%0d to glb start at %0t", kernel.name, i, j,
                     start_time);

            // proc_drv.write_data(kernel.inputs[i].io_tiles[j].start_addr,
            //                     kernel.inputs[i].io_tiles[j].io_block_data);
            PD_wd_start_addr = kernel.inputs[i].io_tiles[j].start_addr;
            PD_wd_data_q = kernel.inputs[i].io_tiles[j].io_block_data;
            ProcDriver_write_data();
            end_time = $realtime;
            $display("[%s] write input_%0d_block_%0d to glb end at %0t", kernel.name, i, j,
                     end_time);
            $display("[%s] It takes %0t time to write %0d Byte data to glb.", kernel.name,
                     end_time - start_time, kernel.inputs[i].io_tiles[j].num_data * 2);
        end
    end
endtask

// task Environment::read_data(Kernel kernel);
data_array_t Env_read_data_data_q;

task Env_read_data();
    repeat (20) @(posedge p_ifc.clk);

    // Fill kernel.outputs() w data from CGRA
    foreach (kernel.outputs[i]) begin
        foreach (kernel.outputs[i].io_tiles[j]) begin
            // 3002ns
            $display("[%s] read output_%0d_block_%0d from glb START", kernel.name, i, j);

            // Creates empty array of indicated size maybe (4096)
            Env_read_data_data_q = new[kernel.outputs[i].io_tiles[j].io_block_data.size()];   // size=4096

            // proc_drv.read_data(kernel.outputs[i].io_tiles[j].start_addr, Env_read_data_data_q);
                PD_rdata_start_addr = kernel.outputs[i].io_tiles[j].start_addr; // 0x1000 or some such
                PD_rdata_data_q = Env_read_data_data_q;
                $display("calling ProcDriver_read_data()");  // 3002ns
                ProcDriver_read_data();

            kernel.outputs[i].io_tiles[j].io_block_data = PD_rdata_data_q;
            $display("[%s] read output_%0d_block_%0d from glb END", kernel.name, i, j);  // 3002ns
        end
    end
endtask

// task Environment::glb_configure(Kernel kernel);
task Env_glb_configure();
    $timeformat(-9, 2, " ns", 0);
    start_time = $realtime;
    $display("[%s] glb configuration start at %0t", kernel.name, start_time);

    // axil_drv.config_write(kernel.bs_cfg);
    // axil_drv.config_write(kernel.kernel_cfg);
    AxilDriver_cfg = kernel.bs_cfg;     AxilDriver_config_write();
    AxilDriver_cfg = kernel.kernel_cfg; AxilDriver_config_write();

    end_time = $realtime;
    $display("[%s] glb configuration end at %0t", kernel.name, end_time);  // ~1500ns
endtask

// task Environment::cgra_configure(Kernel kernel);
Config Env_cgra_configure_cfg;
int group_start, num_groups;

task Env_cgra_configure();
    $timeformat(-9, 2, " ns", 0);
    group_start = kernel.group_start;
    num_groups = kernel.num_groups;

    // glb_stall_mask = calculate_glb_stall_mask(group_start, num_groups); // unused???
    $display("build stall mask"); $fflush();
    Env_cgra_stall_mask = calculate_cgra_stall_mask(group_start, num_groups);

    $display("calling cgra_stall()"); $fflush();
    // cgra_stall(cgra_stall_mask);
    Env_cgra_stall();
    start_time = $realtime;
    $display("[%s] fast configuration start at %0t", kernel.name, start_time);  // 1560ns
    // Writes, maybe, 1'b1 to address 0x1c
    Env_cgra_configure_cfg = kernel.get_pcfg_start_config();

    // axil_drv.write(cfg.addr, cfg.data);
    addr = Env_cgra_configure_cfg.addr;  // 0x1c
    data = Env_cgra_configure_cfg.data;  // 0x01
    AxilDriver_write();

    // wait_interrupt(GLB_PCFG_CTRL, kernel.bs_tile);
    $display("calling wait_interrupt()"); $fflush();
    glb_ctrl = GLB_PCFG_CTRL;    // 0x38
    tile_num   = kernel.bs_tile;
    Env_wait_interrupt();
    $display("returned from wait_interrupt()"); $fflush();

    // TODO should this clear() do anything?
    // For now I have jimmied the stub to pull interrupt high for two cycles then low again
    // clear_interrupt(GLB_PCFG_CTRL, kernel.bs_tile);
    $display("calling clear_interrupt()"); $fflush();
    glb_ctrl = GLB_PCFG_CTRL;    // 0x38
    tile_num   = kernel.bs_tile;
    Env_clear_interrupt();
    $display("returning from clear_interrupt()"); $fflush();

    end_time = $realtime;
    $display("[%s] fast configuration end at %0t", kernel.name, end_time);  // 1710ns
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
bit [CGRA_AXI_DATA_WIDTH-1:0] Env_cgra_stall_data;
bit [CGRA_AXI_DATA_WIDTH-1:0] Env_cgra_stall_wr_data;
// bit [NUM_CGRA_COLS-1:0] Env_cgra_stall_mask;
task Env_cgra_stall();
    // AxilDriver_read(`GLC_CGRA_STALL_R, Env_cgra_stall_data);  // TBD
    AxilDriver_read_addr = `GLC_CGRA_STALL_R;  // 0x8 (glc.svh)
    $display("AxilDriver_read()"); $fflush();
    AxilDriver_read();
    Env_cgra_stall_data = AxilDriver_read_data;

    Env_cgra_stall_wr_data = Env_cgra_stall_mask |
                                     Env_cgra_stall_data;
    // AxilDriver_write(`GLC_CGRA_STALL_R, Env_cgra_stall_wr_data);
    addr = `GLC_CGRA_STALL_R;
    data = Env_cgra_stall_wr_data;
    $display("AxilDriver_write()"); $fflush();
    AxilDriver_write();
    $display("Stall CGRA with stall mask %8h", Env_cgra_stall_mask);
endtask

// task Environment::cgra_unstall(bit [NUM_CGRA_COLS-1:0] stall_mask);
bit [NUM_CGRA_COLS-1:0] Env_cgra_unstall_stall_mask;
bit [CGRA_AXI_DATA_WIDTH-1:0] Env_cgra_unstall_data;
bit [CGRA_AXI_DATA_WIDTH-1:0] Env_cgra_unstall_wr_data;
task Env_cgra_unstall();
    // Unstall CGRA
    Env_cgra_unstall_stall_mask = Env_cgra_stall_mask;
    $display("Welcome to Env_cgra_unstall()"); $fflush();

    // axil_drv.read(`GLC_CGRA_STALL_R, data);
        AxilDriver_read_addr = `GLC_CGRA_STALL_R;
        AxilDriver_read();  // 1850ns
        Env_cgra_unstall_data = AxilDriver_read_data;
    Env_cgra_unstall_wr_data 
      = (~Env_cgra_unstall_stall_mask)
        & Env_cgra_unstall_data;

    // axil_drv.write(`GLC_CGRA_STALL_R, wr_data);
    addr = `GLC_CGRA_STALL_R;
    data = Env_cgra_unstall_wr_data;
    AxilDriver_write();

    // 3970ns
    $display("Unstall CGRA with stall mask %4h", Env_cgra_unstall_stall_mask);
endtask // Env_cgra_unstall

// FIXME/TODO What does this one do?
// task Environment::kernel_test(Kernel kernel);
Config Env_kernel_cfg;
int total_output_size;
// int group_start, num_groups;                 // re-use existing I guess :(
// bit [NUM_GLB_TILES-1:0] glb_stall_mask;   // re-use existing I guess :(
// bit [NUM_CGRA_COLS-1:0] cgra_stall_mask;  // re-use existing I guess :(
// realtime start_time, end_time, g2f_end_time, latency;  // globals :(

task Env_kernel_test();
    $timeformat(-9, 2, " ns", 0);

    group_start = kernel.group_start;
    num_groups = kernel.num_groups;
    Env_glb_stall_mask = calculate_glb_stall_mask(group_start, num_groups);
    Env_cgra_stall_mask = calculate_cgra_stall_mask(group_start, num_groups);

    // cgra_unstall(cgra_stall_mask);
    Env_cgra_unstall();

    start_time = $realtime;
    $display("[%s] kernel start at %0t", kernel.name, start_time);  // 2824ns
    Env_kernel_cfg = kernel.get_strm_start_config();

    // axil_drv.write(cfg.addr, cfg.data);
    addr = Env_kernel_cfg.addr;  // 0x18
    data = Env_kernel_cfg.data;  // 0x10001
    AxilDriver_write();

// unstall_mask: addr=0x18, data=0x10001
// stall_mask:   addr=0x1c, data=0x00001

    foreach (kernel.inputs[i]) begin
        foreach (kernel.inputs[i].io_tiles[j]) begin
            automatic int ii = i;
            automatic int jj = j;
            fork
                begin
                    // wait_interrupt(GLB_STRM_G2F_CTRL, kernel.inputs[ii].io_tiles[jj].tile);
                    $display("calling wait_interrupt(GLB_STRM_G2F_CTRL=0x%0x)",  // 2840ns
                             GLB_STRM_G2F_CTRL); $fflush();
                    glb_ctrl = GLB_STRM_G2F_CTRL;
                    // FIXME tile_num not automatic. Will this be trouble?
                    tile_num = kernel.inputs[ii].io_tiles[jj].tile;
                    Env_wait_interrupt();
                    $display("returned from wait_interrupt()"); $fflush();

                    // clear_interrupt(GLB_STRM_G2F_CTRL, kernel.inputs[ii].io_tiles[jj].tile);
                    // TODO should this clear() do anything?
                    // For now I have jimmied the stub to pull interrupt high for two cycles then low again
                    // clear_interrupt(GLB_PCFG_CTRL, kernel.bs_tile);
                    // 2866ns
                    $display("calling clear_interrupt(GLB_STRM_G2F_CTRL)"); $fflush();
                    glb_ctrl = GLB_STRM_G2F_CTRL;  // 0x30
                    // tile_num   = kernel.inputs[ii].io_tiles[jj].tile;
                    Env_clear_interrupt();
                    $display("returning from clear_interrupt()"); $fflush();  // 2910ns
                end
            join_none
        end
    end
    wait fork;

    g2f_end_time = $realtime;
    // 2909ns
    $display("[%s] GLB-to-CGRA streaming done at %0t", kernel.name, g2f_end_time);

    foreach (kernel.outputs[i]) begin
        foreach (kernel.outputs[i].io_tiles[j]) begin
            automatic int ii = i;
            automatic int jj = j;
            fork
                begin
                    // wait_interrupt(GLB_STRM_F2G_CTRL, kernel.outputs[ii].io_tiles[jj].tile);
                    $display("calling wait_interrupt(GLB_STRM_F2G_CTRL)"); $fflush();  // 2911ns
                    glb_ctrl = GLB_STRM_F2G_CTRL;  // 0x30
                    tile_num = kernel.inputs[ii].io_tiles[jj].tile;
                    Env_wait_interrupt();
                    $display("returned from wait_interrupt()"); $fflush();
                end
            join_none
        end
    end
    wait fork;
//okay to here maybe

    end_time = $realtime;
    $display("[%s] kernel end at %0t", kernel.name, end_time);  // 2934ns
    $display("[%s] It takes %0t total time to run kernel.", kernel.name, end_time - start_time);

    total_output_size = 0;
    foreach (kernel.output_size[i]) begin
        total_output_size += kernel.output_size[i];
    end
    $display("[%s] The size of output is %0d Byte.", kernel.name, total_output_size);

    latency = end_time - g2f_end_time;
    $display("[%s] The initial latency is %0t.", kernel.name, latency);
    $display("[%s] The throughput is %.3f (GB/s).", kernel.name,
             total_output_size / (g2f_end_time - start_time));

    foreach (kernel.outputs[i]) begin
        foreach (kernel.outputs[i].io_tiles[j]) begin
            automatic int ii = i;
            automatic int jj = j;
            fork
                begin
                    // 2934ns
                    // clear_interrupt(GLB_STRM_F2G_CTRL, kernel.outputs[ii].io_tiles[jj].tile);
                    // TODO should this clear() do anything?
                    // For now I have jimmied the stub to pull interrupt high for two cycles then low again
                    // clear_interrupt(GLB_PCFG_CTRL, kernel.bs_tile);
                    $display("calling clear_interrupt(GLB_STRM_F2G_CTRL)"); $fflush();
                    glb_ctrl = GLB_STRM_F2G_CTRL;
                    tile_num   = kernel.inputs[ii].io_tiles[jj].tile;
                    Env_clear_interrupt();
                    $display("returning from clear_interrupt()"); $fflush();
                end
            join_none
        end
    end
    wait fork;

endtask // Env_kernel_test


// task Environment::wait_interrupt(e_glb_ctrl glb_ctrl,
//                                  bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);
// glc.svh:`define GLC_PAR_CFG_G2F_ISR_R 'h38
// glc.svh:`define GLC_STRM_G2F_ISR_R 'h34
// glc.svh:`define GLC_STRM_F2G_ISR_R 'h30
// glc.svh:`define GLC_GLOBAL_ISR_R 'h3c

string reg_name;
// bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
// bit [CGRA_AXI_DATA_WIDTH-1:0] data;
task Env_wait_interrupt();
    $display("Welcome to wait_interrupt..."); $fflush();  // 1600ns, 2870ns
    // which interrupt
    if (glb_ctrl == GLB_PCFG_CTRL) begin
        addr = `GLC_PAR_CFG_G2F_ISR_R;  // 0x38 (1600ns)
        reg_name = "PCFG";
    end else if (glb_ctrl == GLB_STRM_G2F_CTRL) begin
        addr = `GLC_STRM_G2F_ISR_R;     // 0x34 (2870ns)
        reg_name = "STRM_G2F";
    end else begin
        addr = `GLC_STRM_F2G_ISR_R;     // 0x30
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

                // First we gotta getta interrupt
                // 2870ns
                $display("gettum interruptum"); $fflush();
                wait (top.interrupt);
                $display("gottum interruptum"); $fflush();
                // Reading from addr 0x38, expect to see xxxxx1
                // (Jimmied the stub to return 0xfffffff when it sees addr 0x38)
                // axil_drv.read(addr, data);
                AxilDriver_read_addr = addr;
                AxilDriver_read();  // 1850ns
                data = AxilDriver_read_data;

                $display("Looking for interrupt on tile_num %0d", tile_num); $fflush();
                // I guess data is a bit vector showing which tile did the interrupt??
                if (data[tile_num] == 1) begin
                    $display("%s interrupt from tile %0d", reg_name, tile_num);
                    break;
                end
            end
        end
        begin
            // So...this runs forever I guess? and stops things if they run too long...?
            // If things work correctly...? Someone else pulls $finish before this hits error condition?
            // repeat (5_000_000) @(posedge axil_ifc.clk);
            // repeat (1_000_000) @(posedge axil_ifc.clk);
            // $error("@%0t: %m ERROR: Interrupt wait timeout ", $time);
            // $finish;

            // copilot gave me this one
            forever begin
                @(posedge axil_ifc.clk);
                // if ($time > 6_000_000ns) begin  // FIXME this was originally ns I think
                if ($time > 6_000_000ps) begin
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
// Env_clear_interrupt();

// task Environment::clear_interrupt(e_glb_ctrl glb_ctrl, bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);
// bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
// string reg_name;
bit [NUM_GLB_TILES-1:0] tile_mask;
task Env_clear_interrupt();
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
task Env_set_interrupt_on();
    $display("Turn on interrupt enable registers");
    addr = `GLC_GLOBAL_IER_R;      data = 3'b111; AxilDriver_write();
    addr = `GLC_PAR_CFG_G2F_IER_R; data =   1'b1; AxilDriver_write();
    addr = `GLC_STRM_F2G_IER_R;    data =   1'b1; AxilDriver_write();
    addr = `GLC_STRM_G2F_IER_R;    data =   1'b1; AxilDriver_write();
endtask

task Env_run();
    // wait for reset
    $display("environment L350: // wait for reset"); $fflush();  // 100ns
    repeat (20) @(posedge p_ifc.clk);
    $display("environment L352: waited 20 clocks"); $fflush();

    // turn on interrupt
    // env.set_interrupt_on();
    Env_set_interrupt_on();

    if (dpr) begin
        foreach (kernels[i]) begin
            automatic int j = i;
            fork
                begin
                    // env.write_bs(kernels[j]);
                    kernel = kernels[j];
                    Env_write_bs();

                    env.glb_configure(kernel);
                    env.cgra_configure(kernel);
                    env.write_data(kernel);
                    env.kernel_test(kernel);
                    env.read_data(kernel);
                end
            join_none
        end
        wait fork;
    end else begin
        $display("FOOOO dpr FALSE"); $fflush();
        foreach (kernels[i]) begin
            automatic int j = i;
                begin
                    kernel = kernels[j];
                    Env_write_bs();       // env.write_bs(kernels[j]);
                    Env_glb_configure();  // env.glb_configure(kernel);
                    Env_cgra_configure(); // env.cgra_configure(kernel);
                    Env_write_data();     // env.write_data(kernel);
                    Env_kernel_test();    // env.kernel_test(kernel);
                    Env_read_data();      // env.read_data(kernel);
                    //BOOKMARK
                    kernel.compare();
                end
        end
    end

    //env.run();
endtask // tmp_erun


// task Environment::run();
// Short-handle aliases for AxilDriver_write_{addr,data}
// bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
// bit [CGRA_AXI_DATA_WIDTH-1:0] data;

// task Env_run_old();

/*
            // glb_configure(kernels[j]);
            Env_glb_configure();

            // Is this...what runs the program...?
            // cgra_configure(kernels[j]);
            $display(" Env_cgra_configure() BEGIN"); $fflush();  // 1490ns
            Env_cgra_configure();
            $display(" Env_cgra_configure() END"); $fflush();

            // write_data(kernels[j]);
            $display(" Env_write_data() BEGIN"); $fflush();  // 1680ns
            Env_write_data();
            $display(" Env_write_data() END"); $fflush();

            // kernel_test(kernels[j]);
            $display("Env_kernel_test() BEGIN"); $fflush();  // 2722ns
            Env_kernel_test();
            $display("Env_kernel_test() END"); $fflush();    // 2980ns

            // read_data(kernels[j]);
            $display("Env_read_data() BEGIN"); $fflush();    // 2982ns
            Env_read_data();
            $display("Env_read_data() END"); $fflush();      // 4037ns

            // Dumps final output to a file "hw_output.txt" I guess??
            $display("Kernel-compare BEGIN"); $fflush();  // 4037ns
            kernels[j].compare();
            $display("Kernel-compare END"); $fflush();    // 4037ns
        end
        $display("\n...guess what there was %0d kernels...\n", j);
    end
endtask

    $display("FOOO calculate_cgra_stall_mask = %0x", calculate_cgra_stall_mask);
    $display("FOOO num = %0d", num);
    $display("FOOO start = %0x", start);
        $display("FOOO (start + i) * 4 = %0x", (start + i) * 4);
    $display("FOOO2 stall mask cgra_stall_mask still %0x, maybe should be 0x00ff", Env_cgra_stall_mask);
    $display("FOOO3 stall mask cgra_stall_mask still %0x, maybe should be 0x00ff", Env_cgra_stall_mask);
    $display("FOOO4 stall mask cgra_stall_mask still %0x, maybe should be 0x00ff", Env_cgra_stall_mask);
    $display("FOOO1 got stall mask cgra_stall_mask %0x, maybe should be 0x00ff", Env_cgra_stall_mask);

                $display("FOOO tile_num=%0d", tile_num); $fflush();

// okay to here
            $display("Made a queue of size", Env_read_data_data_q.size()); $fflush();
            $display("Copied a queue of size", PD_rdata_data_q.size()); $fflush();
            $display("1 Gonna offload %0d blocks", PD_rdata_data_q.size()); $fflush();
            $display("FOO BEFORE: PD_rdata_data_q.size() = %0d", PD_rdata_data_q.size()); $fflush();

                    // env.write_bs(kernels[j]);
                    // env.glb_configure(kernel);
                    // env.cgra_configure(kernel);
                    // env.write_data(kernel);
                    // env.kernel_test(kernel);
                    // env.read_data(kernel);





*/

// task Environment::compare();
