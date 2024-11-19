// This is a garnet_test.sv "include" file

// How long to wait for streaming; can be as little as 6K for pointwise, 80K for camera pipeline etc.
int MAX_WAIT = 6_000_000;

/*
class Environment;
*/
typedef enum int {
    GLB_PCFG_CTRL,
    GLB_STRM_G2F_CTRL,
    GLB_STRM_F2G_CTRL
} e_glb_ctrl;

`include "tb/ProcDriver.sv"
`include "tb/AxilDriver.sv"

// Kernel kernels[];  // Declared upstream in enclosing scope 'garnet_test.sv'
Kernel kernel;

task one_cy_delay_if_verilator();
`ifdef verilator
    // $display("WARNING adding one extra cycle for verilator run");
    @(posedge axil_ifc.clk);
`endif
endtask // one_cy_delay_if_verilator
    
task one_cy_delay_if_vcs();
`ifndef verilator
    // $display("WARNING adding one extra cycle for vcs run");
    @(posedge axil_ifc.clk);
`endif
endtask // one_cy_delay_if_vcs

/*
function Environment::new(Kernel kernels[], vAxilIfcDriver vifc_axil, vProcIfcDriver vifc_proc, int dpr);

 
 
function void Environment::build();

 
*/ 
// Non-array trace vars, global for waveform debugging
bitstream_entry_t bet0;
int unsigned betdata0, betaddr0;
/*
task Environment::write_bs(Kernel kernel);
*/
task Env_write_bs();
    realtime start_time, end_time;
    $timeformat(-9, 2, " ns", 0);
    repeat (10) @(p_ifc.clk);
    start_time = $realtime;
    $display("[%s] write bitstream to glb start at %0t", kernel.name, start_time);

    // Debugging I hope--look for these signals in the waveform viewer
    bet0 = kernel.bitstream_data[0];
    betaddr0 = kernel.bitstream_data[0].addr;
    betdata0 = kernel.bitstream_data[0].data;
    
    ProcDriver_write_bs_start_addr = kernel.bs_start_addr;
    ProcDriver_write_bs_bs_q = kernel.bitstream_data;
    ProcDriver_write_bs();

    end_time = $realtime;
    $display("[%s] write bitstream to glb end at %0t", kernel.name, end_time);
    $display("[%s] It takes %0t time to write the bitstream to glb.", kernel.name,
             end_time - start_time);
endtask

/*
task Environment::write_data(Kernel kernel);
*/
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

/*
task Environment::read_data(Kernel kernel);
*/
task Env_read_data();
    repeat (20) @(posedge p_ifc.clk);

    // Fill kernel.outputs() w data from CGRA
    foreach (kernel.outputs[i]) begin
        foreach (kernel.outputs[i].io_tiles[j]) begin
            $display("[%s] read output_%0d_block_%0d from glb start", kernel.name, i, j);
            // FIXME: VCS Q-2020.03 Does not support this yet.
            // "Hierarchical reference to a structure array member connected to task ref-port is not supported"
            // proc_drv.read_data(kernel.outputs[i].io_tiles[j].start_addr,
            //                    kernel.outputs[i].io_tiles[j].io_block_data);

            // Creates empty array of indicated size maybe (4096 maybe)
            PD_rdata_data_q = new[kernel.outputs[i].io_tiles[j].io_block_data.size()];
            PD_rdata_start_addr = kernel.outputs[i].io_tiles[j].start_addr; // 0x1000 or some such
            // PD_rdata_data_q = Env_read_data_data_q;
            ProcDriver_read_data();

            kernel.outputs[i].io_tiles[j].io_block_data = PD_rdata_data_q;
            $display("[%s] read output_%0d_block_%0d from glb end", kernel.name, i, j);
        end
    end
endtask

/*
task Environment::glb_configure(Kernel kernel);
*/
task Env_glb_configure();
    realtime start_time, end_time;
    $timeformat(-9, 2, " ns", 0);
    start_time = $realtime;
    $display("[%s] glb configuration start at %0t", kernel.name, start_time);
    AxilDriver_cfg = kernel.bs_cfg;     AxilDriver_config_write();
    AxilDriver_cfg = kernel.kernel_cfg; AxilDriver_config_write();
    end_time = $realtime;
    $display("[%s] glb configuration end at %0t\n", kernel.name, end_time);  // 647.5ns
endtask

// BOOKMARK bookmark
/*
task Environment::cgra_configure(Kernel kernel);
*/
Config Env_cgra_configure_cfg;
int group_start, num_groups;
bit [NUM_GLB_TILES-1:0] tile_mask;
e_glb_ctrl glb_ctrl;

bit [NUM_GLB_TILES-1:0] glb_stall_mask;
bit [NUM_CGRA_COLS-1:0] cgra_stall_mask;

task Env_cgra_configure();
    realtime start_time, end_time;

    $timeformat(-9, 2, " ns", 0);
    group_start = kernel.group_start;
    num_groups = kernel.num_groups;

    cgra_stall_mask = calculate_cgra_stall_mask(group_start, num_groups);
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
    tile_mask = 1 << kernel.bs_tile;
    $display("calling wait_interrupt(GLB_PCFG_CTRL) = 0x38");
    glb_ctrl = GLB_PCFG_CTRL;    // 0x38
    Env_wait_interrupt();
    Env_clear_interrupt();

    end_time = $realtime;
    $display("[%s] fast configuration end at %0t", kernel.name, end_time);  // 1710ns
    $display("[%s] It takes %0t time to do parallel configuration.\n", kernel.name,
             end_time - start_time);
endtask

/*
function bit [NUM_GLB_TILES-1:0] Environment::calculate_glb_stall_mask(int start, int num);
*/
function bit [NUM_GLB_TILES-1:0] calculate_glb_stall_mask(int start, int num);
    calculate_glb_stall_mask = '0;
    for (int i = 0; i < num; i++) begin
        calculate_glb_stall_mask |= ((2'b11) << ((start + i) * 2));
    end
endfunction

/*
function bit [NUM_CGRA_COLS-1:0] Environment::calculate_cgra_stall_mask(int start, int num);
*/
function bit [NUM_CGRA_COLS-1:0] calculate_cgra_stall_mask(int start, int num);
    calculate_cgra_stall_mask = '0;
    for (int i = 0; i < num; i++) begin
        calculate_cgra_stall_mask |= ((4'b1111) << ((start + i) * 4));
    end
endfunction

// task Environment::cgra_stall(bit [NUM_CGRA_COLS-1:0] stall_mask);
bit [CGRA_AXI_DATA_WIDTH-1:0] Env_cgra_stall_data;
bit [CGRA_AXI_DATA_WIDTH-1:0] Env_cgra_stall_wr_data;
// bit [NUM_CGRA_COLS-1:0] cgra_stall_mask;
task Env_cgra_stall();
    // AxilDriver_read(`GLC_CGRA_STALL_R, Env_cgra_stall_data);  // TBD
    addr = `GLC_CGRA_STALL_R;  // 0x8 (glc.svh)
    AxilDriver_read();
    Env_cgra_stall_data = data;

    Env_cgra_stall_wr_data = cgra_stall_mask |
                                     Env_cgra_stall_data;

    // AxilDriver_write(`GLC_CGRA_STALL_R, Env_cgra_stall_wr_data);
    addr = `GLC_CGRA_STALL_R;
    data = Env_cgra_stall_wr_data;
    AxilDriver_write();

    $display("Stall CGRA with stall mask %8h\n", cgra_stall_mask);
endtask

// task Environment::cgra_unstall(bit [NUM_CGRA_COLS-1:0] stall_mask);
bit [NUM_CGRA_COLS-1:0] cgra_unstall_stall_mask;
bit [CGRA_AXI_DATA_WIDTH-1:0] Env_cgra_unstall_data;
bit [CGRA_AXI_DATA_WIDTH-1:0] Env_cgra_unstall_wr_data;
task Env_cgra_unstall();
    // Unstall CGRA
    cgra_unstall_stall_mask = cgra_stall_mask;
    $display("Welcome to Env_cgra_unstall()");

    addr = `GLC_CGRA_STALL_R;
    AxilDriver_read();  // 1850ns
    Env_cgra_unstall_data = data;
    Env_cgra_unstall_wr_data 
      = (~cgra_unstall_stall_mask)
        & Env_cgra_unstall_data;

    // axil_drv.write(`GLC_CGRA_STALL_R, wr_data);
    addr = `GLC_CGRA_STALL_R;  // 0x8, defined in glv.svh maybe
    data = Env_cgra_unstall_wr_data;
    AxilDriver_write();

    // 3970ns
    $display("Unstall CGRA with stall mask %4h", cgra_unstall_stall_mask);
endtask // Env_cgra_unstall

// task Environment::kernel_test(Kernel kernel);
Config Env_kernel_cfg;
int total_output_size;

// FIXME/TODO this could be three subtasks start_streaming(), wait_for_g2f(), wait_for_f2g()
// or glb_stream_g2f() and glb_stream_f2g() or some such
task Env_kernel_test();
    realtime start_time, end_time, g2f_end_time, latency;

    $timeformat(-9, 2, " ns", 0);
    group_start = kernel.group_start;
    num_groups = kernel.num_groups;
    glb_stall_mask = calculate_glb_stall_mask(group_start, num_groups);
    cgra_stall_mask = calculate_cgra_stall_mask(group_start, num_groups);

    // cgra_unstall(cgra_stall_mask);
    Env_cgra_unstall();

    start_time = $realtime;
    $display("[%s] kernel start at %0t", kernel.name, start_time);  // 1831ns (pointwise)
    Env_kernel_cfg = kernel.get_strm_start_config();

    // A write of 0x10001 to address 0x18 starts data streaming to proc tiles.
    // axil_drv.write(cfg.addr, cfg.data);
    addr = Env_kernel_cfg.addr;  // 0x18
    data = Env_kernel_cfg.data;  // (e.g. 0x10001 for pointwise)
    AxilDriver_write();          // This starts the (G2F) streaming

    // Build a mask that shows which tiles are receiving data from GLB
    tile_mask = 0;
    foreach (kernel.inputs[i]) begin
        foreach (kernel.inputs[i].io_tiles[j]) begin
            tile_mask |= 1 << kernel.inputs[i].io_tiles[j].tile;
        end
    end
    $display("\n[%0t] Built a INPUT tile mask %0x", $time, tile_mask);

    // Wait for an interrupt to tell us when input streaming is done
    // Then wait until interrupt mask contains ALL TILES listed in tile_mask
    // Then clear the interrupt(s)

    glb_ctrl = GLB_STRM_G2F_CTRL;
    Env_wait_interrupt();
    Env_clear_interrupt();

    g2f_end_time = $realtime; // 2909ns
    $display("[%s] GLB-to-CGRA streaming done at %0t", kernel.name, g2f_end_time);

    // Build a mask that shows which tiles are sending data to GLB
    tile_mask = 0;
    foreach (kernel.outputs[i]) begin
        foreach (kernel.outputs[i].io_tiles[j]) begin
            tile_mask |= 1 << kernel.outputs[i].io_tiles[j].tile;
        end
    end
    $display("\n[%0t] Built a OUTPUT tile mask %0x", $time, tile_mask);

    // Wait for an interrupt to tell us when output streaming is done
    // Then wait until interrupt mask contains ALL TILES listed in tile_mask
    // Then clear the interrupt(s)

    glb_ctrl = GLB_STRM_F2G_CTRL;  // 0x30
    Env_wait_interrupt();
    Env_clear_interrupt();

    // Summary info for the log

    end_time = $realtime;
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

string reg_name;
bit [$clog2(NUM_GLB_TILES)-1:0] tile_num;
task Env_wait_interrupt();

    $display("Welcome to wait_interrupt...");
    // which interrupt  // TODO this happens at least twice, should it be a task
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

    // Start two parallel threads
    // Return when/if first thread sees interrupts from all tiles in tile_mask
    // If interrupts not all serviced within MAX_WAIT (6M?) clock cycles, error and die

    fork
        begin
            forever begin
                // level sensitive interrupt
                wait (top.interrupt);         // Wait for interrupt, then start checking interrupt mask
                one_cy_delay_if_verilator();  // Vvverilator is off by 1cy here vs. vcs

                // Got an interrupt. One or more tiles have finished streaming.
                // Read the indicated reg to see which one(s) have finished so far.

                AxilDriver_read();
                $display("%s interrupt tiles %0x; waiting for %0x", reg_name, data, tile_mask);
                if (data == 0) begin
                    $display("WARNING got interrupt, but not from %s apparently", reg_name);
                    $display("(this is probably a fatal error ackshully");
                    continue;  // Keep waiting for the RIGHT interrupt
                end
                // Don't stop until interrupt mask (data) contains ALL tiles in tile_mask
                if (data == tile_mask) break;
                break;  // Gotta break out of forever loop, duh
            end
        end
        begin
            // ERROR if we go MAX_WAIT cycles without finding the interrupts
            $display("[%0t] Begin waiting for interrupt on reg %s; MAX_WAIT=%0d",
                     $time, reg_name, MAX_WAIT);

            // Wait for streaming to finish, but don't wait forever.
            // It can take 5M cycles or more for larger runs, see MAX_WAIT above.
            // When/if interrupt clears (above), this loop dies b/c 'join_any'

            // repeat (MAX_WAIT) @(posedge...);  // "repeat" confuses verilator:(
            for (int i=0; i<MAX_WAIT; i++) @(posedge axil_ifc.clk);
            $error("@%0t: %m ERROR: Interrupt wait timeout, waited %0d cy for reg %s", 
                   $time, MAX_WAIT, reg_name);
            $finish(2);  // The "2" prints more information about when/where/why
        end
    join_any
    disable fork;
    $display("[%0t] FORK CANCELLED (right)?", $time);
endtask

task Env_clear_interrupt();

    $display("Welcome to clear_interrupt...");
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
    $display("%s clear ALL RELEVANT TILES(?) using mask", reg_name, tile_mask);

    data = tile_mask;    // Yes this is redundant b/c clear_interrupt() always follows wait_interrupt()
    AxilDriver_write();  // Writes to interrupt reg addr from above
    $display("%s interrupts CLEARED i hope\n", reg_name);
endtask // Env_clear_interrupt


task Env_set_interrupt_on();
    $display("Turn on interrupt enable registers");
    addr = `GLC_GLOBAL_IER_R;      data = 3'b111; AxilDriver_write();
    addr = `GLC_PAR_CFG_G2F_IER_R; data =   1'b1; AxilDriver_write();
    addr = `GLC_STRM_F2G_IER_R;    data =   1'b1; AxilDriver_write();
    addr = `GLC_STRM_G2F_IER_R;    data =   1'b1; AxilDriver_write();
endtask


task Env_run();
    // int dpr;  (declared in garnet_test.sv, which "include"s this file)
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
                $display("[%0t] Processing kernel %0d BEGIN", $time, j);
                kernel = kernels[j];
                Env_write_bs();       // env.write_bs(kernels[j]);
                Env_glb_configure();  // env.glb_configure(kernel);
                Env_cgra_configure(); // env.cgra_configure(kernel);
                Env_write_data();     // env.write_data(kernel);
                Env_kernel_test();    // env.kernel_test(kernel);
                Env_read_data();      $display("[%0t] read_data DONE", $time);
                kernel.compare();
                $display("[%0t] Processing kernel %0d END", $time, j);
            end
        end
    end

endtask // Env_run



/* Unused?
task Environment::compare();
    repeat (20) @(vifc_axil.cbd);
    foreach (kernels[i]) begin
        kernels[i].compare();
    end
endtask
*/
