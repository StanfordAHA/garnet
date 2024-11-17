// class Environment;

// MAX_WAIT is related to how long it takes to read/write data to/from tiles
// When debugging, it's good to limit MAX_WAIT so things don't run too long
// - 6K is good enough for pointwise
// - camera pipeline 2x2 needs more than 6K, I use 80K
// - but 80K is not enough for mat_elemadd etc.
// 
int MAX_WAIT = 6000;
// int MAX_WAIT = 80_000;
// int MAX_WAIT = 6_000_000;

typedef enum int {
    GLB_PCFG_CTRL,
    GLB_STRM_G2F_CTRL,
    GLB_STRM_F2G_CTRL
} e_glb_ctrl;
e_glb_ctrl glb_ctrl;

// int dpr;  // Already declared in garnet_test.sv...

realtime start_time, end_time, g2f_end_time, latency;
Kernel kernel;

bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
bit [CGRA_AXI_DATA_WIDTH-1:0] data;

bit [NUM_GLB_TILES-1:0] Env_glb_stall_mask;
bit [NUM_CGRA_COLS-1:0] Env_cgra_stall_mask;


bit [$clog2(NUM_GLB_TILES)-1:0] tile_num;

`include "tb/ProcDriver.sv"
`include "tb/AxilDriver.sv"

// Non-array trace vars for waveform debugging
bitstream_entry_t bet0;
int unsigned betdata0;
int unsigned betaddr0;

// Convenience tasks to adjust vcs vs. verilator timing

task one_cy_delay_if_verilator();
`ifdef verilator
    // $display("WARNING adding one extra cycle for verilator run");
    @(posedge axil_ifc.clk);
`endif
endtask // one_cy_delay_if_verliator
    
task one_cy_delay_if_vcs();
`ifndef verilator
    // $display("WARNING adding one extra cycle for vcs run");
    @(posedge axil_ifc.clk);
`endif
endtask // one_cy_delay_if_vcs


// task Environment::write_bs(Kernel kernel);
task Env_write_bs();
    $timeformat(-9, 2, " ns", 0);
    repeat (10) @(p_ifc.clk);
    start_time = $realtime;
    $display("[%s] write bitstream to glb start at %0t", kernel.name, start_time);

    // proc_drv  = new(p_ifc, proc_lock);
    // proc_drv.write_bs(kernel.bs_start_addr, kernel.bitstream_data);

    // Debugging I hope
    bet0 = kernel.bitstream_data[0];
    betaddr0 = kernel.bitstream_data[0].addr;
    betdata0 = kernel.bitstream_data[0].data;
    
    ProcDriver_write_bs_start_addr = kernel.bs_start_addr;
    ProcDriver_write_bs_bs_q = kernel.bitstream_data;
    ProcDriver_write_bs();

    end_time = $realtime;
    $display("[%s] write bitstream to glb end at %0t", kernel.name, end_time);
    $display("[%s] It takes %0t time to write the bitstream to glb.\n",
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
            $display("[%s] It takes %0t time to write %0d Byte data to glb.\n", kernel.name,
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
            $display("");
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
    $display("[%s] glb configuration end at %0t\n", kernel.name, end_time);  // 647.5ns
endtask

// task Environment::cgra_configure(Kernel kernel);
Config Env_cgra_configure_cfg;
int group_start, num_groups;

task Env_cgra_configure();
    $timeformat(-9, 2, " ns", 0);
    group_start = kernel.group_start;
    num_groups = kernel.num_groups;

    Env_cgra_stall_mask = calculate_cgra_stall_mask(group_start, num_groups);
    Env_cgra_stall();
    start_time = $realtime;
    $display("[%s] fast configuration start at %0t", kernel.name, start_time);  // 1560ns
    // I think maybe this simply writes 1'b1 to address 0x1c
    Env_cgra_configure_cfg = kernel.get_pcfg_start_config();

    // axil_drv.write(cfg.addr, cfg.data);
    addr = Env_cgra_configure_cfg.addr;  // 0x1c
    data = Env_cgra_configure_cfg.data;  // 0x01
    AxilDriver_write();
    //  wait_interrupt(GLB_PCFG_CTRL, kernel.bs_tile);
    // clear_interrupt(GLB_PCFG_CTRL, kernel.bs_tile);
    $display("calling wait_interrupt(GLB_PCFG_CTRL) = 0x38"); $fflush();
    glb_ctrl = GLB_PCFG_CTRL;    // 0x38
    Env_wait_interrupt();

    end_time = $realtime;
    $display("[%s] fast configuration end at %0t", kernel.name, end_time);  // 1710ns
    $display("[%s] It takes %0t time to do parallel configuration.\n", kernel.name,
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
    AxilDriver_read();
    Env_cgra_stall_data = AxilDriver_read_data;

    Env_cgra_stall_wr_data = Env_cgra_stall_mask |
                                     Env_cgra_stall_data;
    // AxilDriver_write(`GLC_CGRA_STALL_R, Env_cgra_stall_wr_data);
    addr = `GLC_CGRA_STALL_R;
    data = Env_cgra_stall_wr_data;
    AxilDriver_write();
    $display("Stall CGRA with stall mask %8h\n", Env_cgra_stall_mask);
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
    $display("[%s] kernel start at %0t", kernel.name, start_time);  // 1831ns (pointwise)
    Env_kernel_cfg = kernel.get_strm_start_config();

    // A write of 0x10001 to address 0x18 starts data streaming to proc tiles.
    // axil_drv.write(cfg.addr, cfg.data);
    addr = Env_kernel_cfg.addr;  // 0x18
    data = Env_kernel_cfg.data;  // 0x10001 ("begin streaming tile 1"?)
    AxilDriver_write();          // This starts the (G2F) streaming

// unstall_mask: addr=0x18, data=0x10001
// stall_mask:   addr=0x1c, data=0x00001

    // Wait for an interrupt to tell us when the streaming is done
    // These two 'foreach' loops are here to tell us HOW MANY tiles need to stream

    // wait_interrupt() will service whatever interrupt happens next,
    // and then the one after that, and so on until the right number
    // have been found. i think.

    // TODO these two loops could be tasks e.g. glb_stream_g2f() and glb_stream_f2g()
    foreach (kernel.inputs[i]) begin
        foreach (kernel.inputs[i].io_tiles[j]) begin
            automatic int ii = i;
            automatic int jj = j;
            fork
                begin
                    //  wait_interrupt(GLB_STRM_G2F_CTRL, kernel.inputs[ii].io_tiles[jj].tile);
                    // clear_interrupt(GLB_STRM_G2F_CTRL, kernel.inputs[ii].io_tiles[jj].tile);
                    $display("\n[%0t] (i%0d,j%0d) Calling wait_interrupt(GLB_STRM_G2F_CTRL) @ 0x34", $time, ii, jj);  // 5954ns
                    $display("\n[%0t] (t%0d) Calling wait_interrupt(GLB_STRM_G2F_CTRL) @ 0x34",
                             $time, kernel.inputs[ii].io_tiles[jj].tile);  // 5954ns
                    glb_ctrl = GLB_STRM_G2F_CTRL;
                    Env_wait_interrupt();
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
            $display("[%0t] (i%0d,j%0d) Processing interrupts for GLB_STRM_F2G_CTRL (0x30)", $time, i, j);
            glb_ctrl = GLB_STRM_F2G_CTRL;  // 0x30
            fork
                begin
                    one_cy_delay_if_vcs();  // FIXME why is this needed (e.g. for pointwise)
                    //  wait_interrupt(GLB_STRM_F2G_CTRL, kernel.inputs[ii].io_tiles[jj].tile);
                    // clear_interrupt(GLB_STRM_F2G_CTRL, kernel.inputs[ii].io_tiles[jj].tile);
                    Env_wait_interrupt();
                    $display("returned from wait_interrupt()");
                end
            join_none
        end
    end
    wait fork;

    end_time = $realtime;
    $display("\n");  // Note this makes TWO blank lines
    $display("[%s] kernel end at %0t", kernel.name, end_time);  // 5971ns
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

endtask // Env_kernel_test


// task Environment::wait_interrupt(e_glb_ctrl glb_ctrl,
//                                  bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);
// glc.svh:`define GLC_PAR_CFG_G2F_ISR_R 'h38
// glc.svh:`define GLC_STRM_G2F_ISR_R 'h34
// glc.svh:`define GLC_STRM_F2G_ISR_R 'h30
// glc.svh:`define GLC_GLOBAL_ISR_R 'h3c

// Must declare vars OUTSIDE fork b/c verilator is squirrely about declaraions inside.
int i_wait;
bit [NUM_GLB_TILES-1:0] tile_mask;

semaphore interrupt_lock;
initial interrupt_lock = new(1);

string reg_name;
// bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
// bit [CGRA_AXI_DATA_WIDTH-1:0] data;
task Env_wait_interrupt();

    $display("Welcome to wait_interrupt..."); $fflush();  // 1600ns, 2870ns
    // which interrupt
    if (glb_ctrl == GLB_PCFG_CTRL) begin
        addr = `GLC_PAR_CFG_G2F_ISR_R;  // 0x38 - 673ns
        reg_name = "PCFG";
    end else if (glb_ctrl == GLB_STRM_G2F_CTRL) begin
        addr = `GLC_STRM_G2F_ISR_R;     // 0x34 - 1839ns
        reg_name = "STRM_G2F";
    end else begin
        addr = `GLC_STRM_F2G_ISR_R;     // 0x30 - 5962ns
        reg_name = "STRM_F2G";
    end

    // So...this does what? Starts two parallel threads?
    // When/if first thread gets and interrupt, we return?
    // ANd ALSO if no interrupt (or finish) after 6M cycles, we error and die?
    // Maybe...'join_any' means fork is complete when/if any subthread finishes??

    // Wait for the next interrupt of the indicated type (e.g. GLB_PCFG_CTRL)
    // regardless of which tile it comes from. What's important is that we get ALL
    // the interrupts, not so much what order in which they arrive. I.e. the calling
    // routine will loop until the right number of interrupts happen.Right?

    fork
        begin
            forever begin
                // level sensitive interrupt

                // First we gotta getta interrupt
                wait (top.interrupt);
                one_cy_delay_if_verilator();  // Off-by-one before this wait

                // Exclusion zone keeps everyone from clearing the same interrupt all at once maybe
                interrupt_lock.get(1);

                // Got an interrupt. Some tile has finished streaming.
                // Read the indicated reg to see which one. Then clear it why not.

                // FIXME wait...AxilDriver_read() uses AxilDriver_read_addr but
                // AxilDriver_write just uses "addr"? This is an unpleasant asymmetry :(

                // axil_drv.read(addr, data);
                AxilDriver_read_addr = addr;
                AxilDriver_read();
                data = AxilDriver_read_data;

                // There maybe be multiple interrupts all at once e.g. if
                // data = 0xfff that means we got interrupts on tiles 0-11/
                // "Exclusion zone" see above prevents everyone from clearing the same tile

                $display("Looking for interrupt on ANY TILE");
                if (data == 0) begin
                    $display("WARNING got interrupt, but not from %s apparently", reg_name);
                    continue;  // Keep waiting for the RIGHT interrupt
                end
/*
                else begin
                    $display("%s interrupt tiles %0x", reg_name, data);
                    for (tile_num=0; tile_num<NUM_GLB_TILES; tile_num++) begin
                        // Clear (one of) the interrupting tile(s)
                        tile_mask = (1 << tile_num);
                        $display("Check tile_num %0d using mask %0x"
                        if ((data[tile_num] & tile_mask) != 0) begin
                            $display("%s clearing tile %0d using mask", reg_name, tile_num, tile_mask);
                            break;
                        end
                    end
                end
*/
                else begin
                    // Find lowest-numbered interrupting tile
                    $display("%s interrupt tiles %0x", reg_name, data);
                    for (tile_num=0; tile_num<NUM_GLB_TILES; tile_num++) begin
                        if (data[tile_num] == 1) break;
                        else continue;
                        $display("ERROR this should be impossible!!?");
                        $finish(2);  // "2" gives time, location, and mem stats
                    end
                end

                // Clear interrupt from the chosen tile 'tile_num'
                tile_mask = (1 << tile_num);
                $display("%s clearing tile %0d using mask", reg_name, tile_num, tile_mask);

                // AxilDriver_write(addr, tile_mask);
                // FIXME wait...AxilDriver_read() uses AxilDriver_read_addr but
                // AxilDriver_write just uses "addr"? This is an unpleasant asymmetry :(
                $display("%s clearing tile %0d using mask", reg_name, tile_num, tile_mask);
                $display("%s interrupt clear\n", reg_name);
                data = tile_mask;
                AxilDriver_write();  // Writes to interrupt reg addr from above
                $display("%s interrupt CLEARED\n", reg_name);

                interrupt_lock.put(1);  // End exclusion zone

                break;  // Gotta break out of forever loop, duh
            end
        end
        begin
            $display("[%0t] FOO begin waiting on reg %s; MAX_WAIT=%0d", reg_name, MAX_WAIT);
            
            // Wait for streaming to finish, but don't wait forever.
            // It can take 5M cycles or more for larger runs, see MAX_WAIT above.
            // When/if interrupt clears (above), this loop dies b/c 'join_any'

            // repeat (MAX_WAIT) @(posedge...);  // "repeat" confuses verilator:(

            // Oh boy it sure was dumb to try and use a global signal for the iterator :(
            // for (i_wait = 0; i_wait < MAX_WAIT; i_wait++) begin
            for (int = 0; i < MAX_WAIT; i++) @(posedge axil_ifc.clk);

            $display("[%0t] FOO timeout waiting on reg %s", reg_name);
            $error("@%0t: %m ERROR: Interrupt wait timeout, waited %0d cy for reg %s", $time, i_wait, reg_name);
            $finish;
        end
    join_any
    disable fork;
    $display("[%0t] FORK CANCELLED (right)?", $time);
endtask

// task Environment::clear_interrupt(e_glb_ctrl glb_ctrl, bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);
// Note clear_interrupt functionality is now embedded as part of wait_interrupt()

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
    $display("[%0t] wait for reset", $time);  // 100ps
    repeat (20) @(posedge p_ifc.clk);

    // turn on interrupt
    $display("[%0t] turn on interrupt", $time);  // 120ps?
    Env_set_interrupt_on();

    if (dpr) begin
        $display("ERROR this version of testbench does not support dpr TRUE");
        $finish(2);  // The only choices are 0,1,2; note $finish() is more drastic than $exit()
        foreach (kernels[i]) begin
            automatic int j = i;
            fork
                begin
                    // env.write_bs(kernels[j]);
                    kernel = kernels[j];
                    Env_write_bs();       // env.write_bs(kernels[j]);
                    Env_glb_configure();  // env.glb_configure(kernel);
                    Env_cgra_configure(); // env.cgra_configure(kernel);
                    Env_write_data();     // env.write_data(kernel);
                    Env_kernel_test();    // env.kernel_test(kernel);
                    Env_read_data();      // env.read_data(kernel);
                end
            join_none
        end
        wait fork;
    end else begin
        $display("\n[%0t] dpr FALSE\n", $time);
        foreach (kernels[i]) begin
            automatic int j = i;
            begin
                $display("[%0t] FOO process kernel %0d BEGIN", $time, j);
                kernel = kernels[j];
                Env_write_bs();       // env.write_bs(kernels[j]);
                Env_glb_configure();  // env.glb_configure(kernel);
                Env_cgra_configure(); // env.cgra_configure(kernel);
                Env_write_data();     // env.write_data(kernel);
                Env_kernel_test();    // env.kernel_test(kernel);
                Env_read_data();      $display("[%0t] read_data DONE", $time);
                kernel.compare();
                $display("[%0t] FOO process kernel %0d END", $time, j);
            end
        end
    end

endtask // Env_run


// task Environment::compare();
/*
    local_bs_q = kernel.parse_bitstream;
    bet0 = local_bs_q[0];
    betdata0 = local_bs_q[0].data;
    ProcDriver_write_bs_bs_q = local_bs_q;
*/

// glb_stall_mask = calculate_glb_stall_mask(group_start, num_groups); // unused???
// $display("build stall mask"); $fflush();
// $display("calling cgra_stall()"); $fflush();
// cgra_stall(cgra_stall_mask);
// $display("returned from wait_interrupt()"); $fflush();
// $display("calling clear_interrupt()"); $fflush();
// $display("returning from clear_interrupt()"); $fflush();
// $display("returned from wait_interrupt()"); $fflush();
// $display("gettum interruptum"); $fflush();
// $display("gottum interruptum"); $fflush();
