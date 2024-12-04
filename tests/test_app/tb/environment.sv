/*=============================================================================
** Module: environemnet.sv
** Description:
**              program to drive garnet testbench
** Author: Keyi Zhang, Taeyoung Kong
** Change history:  10/25/2020 - Implement the first version
**===========================================================================*/

// How long to wait for streaming; can be as little as 6K for pointwise, 80K for camera pipeline etc.
int MAX_WAIT = 6_000_000;

// Not used (yet).
// This block of code (tasks and global signals)
// were added to prepare for the verilator upgrade

typedef enum int {
    GLB_PCFG_CTRL,
    GLB_STRM_G2F_CTRL,
    GLB_STRM_F2G_CTRL
} e_glb_ctrl;

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

// Non-array trace vars, global for waveform debugging
bitstream_entry_t bet0;
int unsigned betdata0, betaddr0;

bit [GLB_ADDR_WIDTH-1:0] start_addr;
bit [GLB_ADDR_WIDTH-1:0] cur_addr;
bitstream_t              bs_q;
data_array_t data_q;

class Environment;
    typedef enum int {
        GLB_PCFG_CTRL,
        GLB_STRM_G2F_CTRL,
        GLB_STRM_F2G_CTRL
    } e_glb_ctrl;

    vAxilIfcDriver vifc_axil;
    vProcIfcDriver vifc_proc;

    Kernel kernels[];
    semaphore proc_lock;
    semaphore axil_lock;

    ProcDriver proc_drv;
    AxilDriver axil_drv;

    int dpr;

    extern function new(Kernel kernels[], vAxilIfcDriver vifc_axil, vProcIfcDriver vifc_proc, int dpr);
    extern function void build();
    extern task write_bs(Kernel kernel);
    extern task write_data(Kernel kernel);
    extern task glb_configure(Kernel kernel);
    extern task cgra_configure(Kernel kernel);
    extern task set_interrupt_on();
    extern task wait_interrupt(e_glb_ctrl glb_ctrl, bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);
    extern task clear_interrupt(e_glb_ctrl glb_ctrl, bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);
    extern task kernel_test(Kernel kernel);
    extern task read_data(Kernel kernel);
  
    extern function bit [NUM_CGRA_COLS_INCLUDING_IO-1:0] calculate_cgra_stall_mask(int start, int num);
    // extern function bit [NUM_GLB_TILES-1:0] calculate_glb_stall_mask(int start, int num);  // UNUSED?
    extern task cgra_stall(bit [NUM_CGRA_COLS_INCLUDING_IO-1:0] stall_mask);
    extern task cgra_unstall(bit [NUM_CGRA_COLS_INCLUDING_IO-1:0] stall_mask);

    extern task run();
    extern task compare();
endclass

function Environment::new(Kernel kernels[], vAxilIfcDriver vifc_axil, vProcIfcDriver vifc_proc, int dpr);
    this.kernels   = kernels;
    this.vifc_axil = vifc_axil;
    this.vifc_proc = vifc_proc;
    this.dpr = dpr;
endfunction

function void Environment::build();
    proc_lock = new(1);
    axil_lock = new(1);
    proc_drv  = new(vifc_proc, proc_lock);
    axil_drv  = new(vifc_axil, axil_lock);
endfunction

task Environment::write_bs(Kernel kernel);
    realtime start_time, end_time;
    $timeformat(-9, 2, " ns", 0);
    repeat (10) @(vifc_proc.cbd);
    start_time = $realtime;
    $display("[%s] write bitstream to glb start at %0t", kernel.name, start_time);

    // Debugging I hope--look for these signals in the waveform viewer
    bet0 = kernel.bitstream_data[0];
    betaddr0 = kernel.bitstream_data[0].addr;
    betdata0 = kernel.bitstream_data[0].data;
    
    start_addr = kernel.bs_start_addr;
    bs_q = kernel.bitstream_data;
    proc_drv.write_bs(kernel.bs_start_addr, kernel.bitstream_data);
    end_time = $realtime;
    $display("[%s] write bitstream to glb end at %0t", kernel.name, end_time);
    $display("[%s] It takes %0t time to write the bitstream to glb.", kernel.name,
             end_time - start_time);
endtask

task Environment::write_data(Kernel kernel);
    realtime start_time, end_time;
    $timeformat(-9, 2, " ns", 0);
    repeat (10) @(vifc_proc.cbd);
    foreach (kernel.inputs[i]) begin
        foreach (kernel.inputs[i].io_tiles[j]) begin
            if (kernel.inputs[i].io_tiles[j].is_glb_input == 1) begin
                // Skip writing input data that is already in GLB
                continue;
            end
            start_time = $realtime;
            $display("[%s] write input_%0d_block_%0d to glb start at %0t", kernel.name, i, j,
                     start_time);
            data_q = kernel.inputs[i].io_tiles[j].io_block_data;
            start_addr = kernel.inputs[i].io_tiles[j].start_addr;
            proc_drv.write_data(kernel.inputs[i].io_tiles[j].start_addr,
                                kernel.inputs[i].io_tiles[j].io_block_data);
            end_time = $realtime;
            $display("[%s] write input_%0d_block_%0d to glb end at %0t", kernel.name, i, j,
                     end_time);
            $display("[%s] It takes %0t time to write %0d Byte data to glb.", kernel.name,
                     end_time - start_time, kernel.inputs[i].io_tiles[j].num_data * 2);
        end
    end
endtask

task Environment::read_data(Kernel kernel);
    data_array_t data_q;
    repeat (20) @(vifc_proc.cbd);

    // Fill kernel.outputs() w data from CGRA
    foreach (kernel.outputs[i]) begin
        foreach (kernel.outputs[i].io_tiles[j]) begin
            $display("[%s] read output_%0d_block_%0d from glb start", kernel.name, i, j);
            // FIXME: VCS Q-2020.03 Does not support this yet.
            // "Hierarchical reference to a structure array member connected to task ref-port is not supported"
            // proc_drv.read_data(kernel.outputs[i].io_tiles[j].start_addr,
            //                    kernel.outputs[i].io_tiles[j].io_block_data);

            // Creates empty array of indicated size maybe (4096 maybe)
            start_addr = kernel.outputs[i].io_tiles[j].start_addr; // 0x1000 or some such
            data_q = new[kernel.outputs[i].io_tiles[j].io_block_data.size()];
            proc_drv.read_data(kernel.outputs[i].io_tiles[j].start_addr, data_q);
            kernel.outputs[i].io_tiles[j].io_block_data = data_q;
            $display("[%s] read output_%0d_block_%0d from glb end", kernel.name, i, j);
        end
    end
endtask

task Environment::glb_configure(Kernel kernel);
    realtime start_time, end_time;
    $timeformat(-9, 2, " ns", 0);
    start_time = $realtime;
    $display("[%s] glb configuration start at %0t", kernel.name, start_time);
    axil_drv.config_write(kernel.bs_cfg);
    axil_drv.config_write(kernel.kernel_cfg);
    end_time = $realtime;
    $display("[%s] glb configuration end at %0t", kernel.name, end_time);
endtask

// Global signals are easier to track than hidden class-automatics...
bit [NUM_GLB_TILES-1:0] tile_mask;
e_glb_ctrl glb_ctrl;
Config cfg;
int group_start, num_groups;
bit [NUM_CGRA_COLS_INCLUDING_IO-1:0] cgra_stall_mask;

task Environment::cgra_configure(Kernel kernel);
    realtime start_time, end_time;
    $timeformat(-9, 2, " ns", 0);

    group_start = kernel.group_start;
    num_groups = kernel.num_groups;
    // glb_stall_mask = calculate_glb_stall_mask(group_start, num_groups);  // UNUSED!
    cgra_stall_mask = calculate_cgra_stall_mask(group_start, num_groups);

    cgra_stall(cgra_stall_mask);
    start_time = $realtime;
    $display("[%s] fast configuration start at %0t", kernel.name, start_time);
    cfg = kernel.get_pcfg_start_config();  // This just writes 1'b1 to address 0x1c maybe?

    addr = cfg.addr;  // 0x1c
    data = cfg.data;  // 0x01
    axil_drv.write(cfg.addr, cfg.data);

    $display("calling wait_interrupt(GLB_PCFG_CTRL) = 0x38");
    tile_mask = 1 << kernel.bs_tile;

    wait_interrupt(GLB_PCFG_CTRL, kernel.bs_tile);
    clear_interrupt(GLB_PCFG_CTRL, kernel.bs_tile);
    end_time = $realtime;
    $display("[%s] fast configuration end at %0t", kernel.name, end_time);
    $display("[%s] It takes %0t time to do parallel configuration.", kernel.name,
             end_time - start_time);

endtask

/* UNUSED???
function bit [NUM_GLB_TILES-1:0] Environment::calculate_glb_stall_mask(int start, int num);
    calculate_glb_stall_mask = '0;
    for (int i = 0; i < num; i++) begin
        calculate_glb_stall_mask |= ((2'b11) << ((start + i) * 2));
    end
endfunction
*/

function bit [NUM_CGRA_COLS_INCLUDING_IO-1:0] Environment::calculate_cgra_stall_mask(int start, int num);
    calculate_cgra_stall_mask = '0;
    for (int i = 0; i < num; i++) begin
        calculate_cgra_stall_mask |= ((4'b1111) << ((start + i) * 4));
    end

    if (NUM_CGRA_COLS_INCLUDING_IO != NUM_CGRA_COLS) begin
        calculate_cgra_stall_mask = (calculate_cgra_stall_mask << 1) | 1'b1;
    end
endfunction


bit [NUM_CGRA_COLS_INCLUDING_IO-1:0] stall_mask;
bit [CGRA_AXI_DATA_WIDTH-1:0] Env_cgra_stall_data;
bit [CGRA_AXI_DATA_WIDTH-1:0] Env_cgra_stall_wr_data;

  task Environment::cgra_stall(bit [NUM_CGRA_COLS_INCLUDING_IO-1:0] stall_mask);
    // Stall CGRA
    axil_drv.read(`GLC_CGRA_STALL_R, data);
    wr_data = stall_mask | data;
    Env_cgra_stall_wr_data = stall_mask | data;
    addr = `GLC_CGRA_STALL_R;
    data = Env_cgra_stall_wr_data;
    axil_drv.write(`GLC_CGRA_STALL_R, wr_data);

    $display("Stall CGRA with stall mask %8h", stall_mask);
endtask


bit [CGRA_AXI_DATA_WIDTH-1:0] wr_data;
  task Environment::cgra_unstall(bit [NUM_CGRA_COLS_INCLUDING_IO-1:0] stall_mask);
    // Unstall CGRA
    axil_drv.read(`GLC_CGRA_STALL_R, data);
    wr_data = (~stall_mask) & data;
    addr = `GLC_CGRA_STALL_R;  // 0x8, defined in glv.svh maybe
    data = wr_data;
    axil_drv.write(`GLC_CGRA_STALL_R, wr_data);

    $display("Unstall CGRA with stall mask %4h", stall_mask);
endtask

Config Env_kernel_cfg;
int total_output_size;

// FIXME/TODO this could be three subtasks start_streaming(), wait_for_g2f(), wait_for_f2g()
// or glb_stream_g2f() and glb_stream_f2g() or some such
task Environment::kernel_test(Kernel kernel);
    realtime start_time, end_time, g2f_end_time, latency;
    $timeformat(-9, 2, " ns", 0);

    group_start = kernel.group_start;
    num_groups = kernel.num_groups;
    // glb_stall_mask = calculate_glb_stall_mask(group_start, num_groups);  // UNUSED?
    cgra_stall_mask = calculate_cgra_stall_mask(group_start, num_groups);
    cgra_unstall(cgra_stall_mask);

    start_time = $realtime;
    $display("[%s] kernel start at %0t", kernel.name, start_time);
    cfg = kernel.get_strm_start_config();

    // A write of 0x10001 to address 0x18 starts data streaming to proc tiles.
    addr = Env_kernel_cfg.addr;  // 0x18
    data = Env_kernel_cfg.data;  // (e.g. 0x10001 for pointwise)
    axil_drv.write(cfg.addr, cfg.data);

    // Wait for an interrupt to tell us when input streaming is done
    // Then wait until interrupt mask contains ALL TILES listed in tile_mask
    // Then clear the interrupt(s)

    foreach (kernel.inputs[i]) begin
        foreach (kernel.inputs[i].io_tiles[j]) begin
            automatic int ii = i;
            automatic int jj = j;
            fork
                begin
                    wait_interrupt(GLB_STRM_G2F_CTRL, kernel.inputs[ii].io_tiles[jj].tile);
                    clear_interrupt(GLB_STRM_G2F_CTRL, kernel.inputs[ii].io_tiles[jj].tile);
                end
            join_none
        end
    end
    wait fork;

    g2f_end_time = $realtime;
    $display("[%s] GLB-to-CGRA streaming done at %0t", kernel.name, g2f_end_time);

    // Wait for an interrupt to tell us when output streaming is done
    // Then wait until interrupt mask contains ALL TILES listed in tile_mask
    // Then clear the interrupt(s)

    foreach (kernel.outputs[i]) begin
        foreach (kernel.outputs[i].io_tiles[j]) begin
            automatic int ii = i;
            automatic int jj = j;
            fork
                begin
                    wait_interrupt(GLB_STRM_F2G_CTRL, kernel.outputs[ii].io_tiles[jj].tile);
                end
            join_none
        end
    end
    wait fork;

    end_time = $realtime;
    $display("[%s] kernel end at %0t", kernel.name, end_time);
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
                    clear_interrupt(GLB_STRM_F2G_CTRL, kernel.outputs[ii].io_tiles[jj].tile);
                end
            join_none
        end
    end
    wait fork;

endtask

// Register defs in glc.svh
//  `define GLC_PAR_CFG_G2F_ISR_R 'h38
//  `define GLC_STRM_G2F_ISR_R    'h34
//  `define GLC_STRM_F2G_ISR_R    'h30
//  `define GLC_GLOBAL_ISR_R      'h3c

string reg_name;
task Environment::wait_interrupt(e_glb_ctrl glb_ctrl, bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);

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

    // Start two parallel threads
    // Return when/if first thread sees interrupts from all tiles in tile_mask
    // If interrupts not all serviced within MAX_WAIT (6M?) clock cycles, error and die

    fork
        begin
            forever begin
                // level sensitive interrupt
                wait (top.interrupt);

                // Got an interrupt. One or more tiles have finished streaming.
                // Read the interrupt register to see which one(s) have finished so far.

                axil_drv.read(addr, data);
                $display("%s interrupt tiles %0x; waiting to see %0x", reg_name, data, tile_mask);
                if (data == 0) begin
                    $display("WARNING got interrupt, but not from %s apparently", reg_name);
                    $display("(this is probably a fatal error ackshully");
                    continue;  // Keep waiting for the RIGHT interrupt
                end
                if (data[tile_num] == 1) begin
                    $display("%s interrupt from tile %0d", reg_name, tile_num);
                    break;
                end
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

task Environment::clear_interrupt(e_glb_ctrl glb_ctrl, bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);
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
    axil_drv.write(addr, tile_mask);
endtask

task Environment::set_interrupt_on();
    $display("Turn on interrupt enable registers");
    axil_drv.write(`GLC_GLOBAL_IER_R, 3'b111);
    axil_drv.write(`GLC_PAR_CFG_G2F_IER_R, {NUM_GLB_TILES{1'b1}});
    axil_drv.write(`GLC_STRM_F2G_IER_R, {NUM_GLB_TILES{1'b1}});
    axil_drv.write(`GLC_STRM_G2F_IER_R, {NUM_GLB_TILES{1'b1}});
endtask

task Environment::run();
    // wait for reset
    repeat (20) @(vifc_proc.cbd);

    // turn on interrupt
    $display("[%0t] wait for reset", $time);  // 100ps
    set_interrupt_on();

    if (dpr) begin
        $display("ERROR we no longer support dpr TRUE; we're not even sure when/if it was ever used");
        $finish(2);
        foreach (kernels[i]) begin
            automatic int j = i;
            fork
                begin
                    write_bs(kernels[j]);
                    glb_configure(kernels[j]);
                    cgra_configure(kernels[j]);
                    write_data(kernels[j]);
                    kernel_test(kernels[j]);
                    read_data(kernels[j]);
                end
            join_none
        end
        wait fork;
    end else begin
        foreach (kernels[i]) begin
            automatic int j = i;
                begin
                $display("[%0t] Processing kernel %0d BEGIN", $time, j);
                    write_bs(kernels[j]);
                    glb_configure(kernels[j]);
                    cgra_configure(kernels[j]);
                    write_data(kernels[j]);
                    kernel_test(kernels[j]);
                    read_data(kernels[j]);
                    kernels[j].compare();
                $display("[%0t] Processing kernel %0d END", $time, j);
                end
        end
    end
endtask

task Environment::compare();
    repeat (20) @(vifc_axil.cbd);
    foreach (kernels[i]) begin
        kernels[i].compare();
    end
endtask
