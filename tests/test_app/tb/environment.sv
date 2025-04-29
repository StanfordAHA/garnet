// This is a garnet_test.sv "include" file

// How long to wait for streaming; can be as little as 6K for pointwise, 80K for camera pipeline etc.
int MAX_WAIT = 6_000_000;

typedef enum int {
    GLB_PCFG_CTRL,
    GLB_STRM_G2F_CTRL,
    GLB_STRM_F2G_CTRL
} e_glb_ctrl;

`include "tb/proc_driver.sv"
`include "tb/axil_driver.sv"

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

    start_addr = kernel.bs_start_addr;
    bs_q = kernel.bitstream_data;
    ProcDriver_write_bs();

    end_time = $realtime;
    $display("[%s] write bitstream to glb end at %0t", kernel.name, end_time);
    $display("[%s] It takes %0t time to write the bitstream to glb.", kernel.name,
             end_time - start_time);
endtask

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
            start_addr = kernel.inputs[i].io_tiles[j].start_addr;
            data_q = kernel.inputs[i].io_tiles[j].io_block_data;
            ProcDriver_write_data();
            end_time = $realtime;
            $display("[%s] write input_%0d_block_%0d to glb end at %0t", kernel.name, i, j,
                     end_time);
            $display("[%s] It takes %0t time to write %0d Byte data to glb.", kernel.name,
                     end_time - start_time, kernel.inputs[i].io_tiles[j].num_data * 2);
        end
    end
endtask

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
            data_q = new[kernel.outputs[i].io_tiles[j].io_block_data.size()];
            start_addr = kernel.outputs[i].io_tiles[j].start_addr; // 0x1000 or some such
            ProcDriver_read_data();

            kernel.outputs[i].io_tiles[j].io_block_data = data_q;
            $display("[%s] read output_%0d_block_%0d from glb end", kernel.name, i, j);
        end
    end
endtask


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


task Env_mu_configure();
    realtime start_time, end_time;
    $timeformat(-9, 2, " ns", 0);
    start_time = $realtime;
    $display("[%s] MU configuration start at %0t", kernel.name, start_time);
    mu_serialized_params = dnn_layer.serialized_matrix_params;
    MU_AxilDriver_serialized_params_write();

    // input base address
    mu_axi_addr = `MU_AXI_INPUT_BASE_R;
    mu_axi_data = 0;
    MU_AxilDriver_write();

   // weight base address
    mu_axi_addr = `MU_AXI_WEIGHT_BASE_R;
    mu_axi_data = 0;
    MU_AxilDriver_write();

    // bias base address
    mu_axi_addr = `MU_AXI_BIAS_BASE_R;
    mu_axi_data = 0;
    MU_AxilDriver_write();


    end_time = $realtime;
    $display("[%s] MU configuration end at %0t\n", kernel.name, end_time);
endtask


bit [NUM_GLB_TILES-1:0] tile_mask;
e_glb_ctrl glb_ctrl;
Config cfg;
int group_start, num_groups;
bit [NUM_CGRA_COLS_INCLUDING_IO-1:0] cgra_stall_mask;
task Env_cgra_configure();

    realtime start_time, end_time;
    $timeformat(-9, 2, " ns", 0);

    group_start = kernel.group_start;
    num_groups = kernel.num_groups;
    cgra_stall_mask = calculate_cgra_stall_mask(group_start, num_groups);

    Env_cgra_stall();
    start_time = $realtime;
    $display("[%s] fast configuration start at %0t", kernel.name, start_time);
    cfg = kernel.get_pcfg_start_config();  // This just writes 1'b1 to address 0x1c maybe?

    addr = cfg.addr;  // 0x1c
    data = cfg.data;  // 0x01
    AxilDriver_write();

    $display("calling wait_interrupt(GLB_PCFG_CTRL) = 0x38");
    tile_mask = 1 << kernel.bs_tile;
    glb_ctrl = GLB_PCFG_CTRL;    // 0x38
    Env_wait_interrupt();
    Env_clear_interrupt();

    end_time = $realtime;
    $display("[%s] fast configuration end at %0t", kernel.name, end_time);
    $display("[%s] It takes %0t time to do parallel configuration.", kernel.name,
             end_time - start_time);
endtask

function bit [NUM_CGRA_COLS_INCLUDING_IO-1:0] calculate_cgra_stall_mask(int start, int num);
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
task Env_cgra_stall();
    stall_mask = cgra_stall_mask;
    // Stall CGRA
    addr = `GLC_CGRA_STALL_R;  // 0x8 (glc.svh)
    AxilDriver_read();
    Env_cgra_stall_wr_data = stall_mask | data;
    addr = `GLC_CGRA_STALL_R;
    data = Env_cgra_stall_wr_data;
    AxilDriver_write();

    $display("Stall CGRA with stall mask %8h", stall_mask);
endtask


bit [CGRA_AXI_DATA_WIDTH-1:0] wr_data;
task Env_cgra_unstall();
    $display("Welcome to Env_cgra_unstall()");
    // Unstall CGRA
    addr = `GLC_CGRA_STALL_R;
    AxilDriver_read();  // read() result gets stored in 'data'
    stall_mask = cgra_stall_mask;
    wr_data = (~stall_mask) & data;
    addr = `GLC_CGRA_STALL_R;  // 0x8, defined in glv.svh maybe
    data = wr_data;
    AxilDriver_write();

    $display("Unstall CGRA with stall mask %4h", stall_mask);
endtask // Env_cgra_unstall


task Behavioral_MU_write_to_cgra();
    realtime start_time, end_time;
    fork
        begin
            // There should only be one MU input for now (and it is unrolled across several IO tiles below)
            foreach (kernel.mu_inputs[i]) begin
                foreach (kernel.mu_inputs[i].io_tiles[j]) begin
                    mu_data_q[j] = kernel.mu_inputs[i].io_tiles[j].io_block_data;
                end
            end

            start_time = $realtime;
            $display("[%s] Behavioral MU writes to CGRA starting at %0t", kernel.name, start_time);
            Behavioral_MU_driver_write_data();
            end_time = $realtime;
            $display("[%s] Behavioral MU write to CGRA ends at %0t", kernel.name, end_time);
            $display("[%s] It takes %0t time for behavioral MU to write %0d Byte data to CGRA.", kernel.name,
                    end_time - start_time, kernel.mu_inputs[0].io_tiles[0].num_data * 2);
        end

        begin
            // ERROR if we go MAX_WAIT cycles without finishing streaming the MU inputs
            for (int i=0; i<MAX_WAIT; i++) @(posedge behavioral_mu_ifc.clk);
            $error("@%0t: %m ERROR: Behavioral MU stream wait timeout, waited %0d cy to finish streaming MU inputs",
                   $time, MAX_WAIT);
            $finish(2);  // The "2" prints more information about when/where/why
        end
    join_any
endtask


Config Env_kernel_cfg;
int total_output_size;
// FIXME/TODO this could be three subtasks start_streaming(), wait_for_g2f(), wait_for_f2g()
// or glb_stream_g2f() and glb_stream_f2g() or some such
task Env_kernel_test();
    realtime start_time, end_time, g2f_end_time, mu2cgra_end_time, latency;
    $timeformat(-9, 2, " ns", 0);
    group_start = kernel.group_start;
    num_groups = kernel.num_groups;
    // glb_stall_mask = calculate_glb_stall_mask(group_start, num_groups); // Unused???
    cgra_stall_mask = calculate_cgra_stall_mask(group_start, num_groups);
    Env_cgra_unstall();

    start_time = $realtime;
    $display("[%s] kernel start at %0t", kernel.name, start_time);
    Env_kernel_cfg = kernel.get_strm_start_config();

    // A write of 0x10001 to address 0x18 starts data streaming to proc tiles.
    addr = Env_kernel_cfg.addr;  // 0x18
    data = Env_kernel_cfg.data;  // (e.g. 0x10001 for pointwise)
    AxilDriver_write();          // This starts the (G2F) streaming

    /* temp registration block for pr diff
    axil_drv.write(cfg.addr, cfg.data);
    */

    // FORK BRANCH 1: Behavioral MU writes data to CGRA
    fork
        begin
            //TODO: Explain this magic number 7 from the RTL. Possibly add regs to solve this in real design.
            if (kernel.app_type != GLB2CGRA && !external_mu_active) begin
                repeat (7) @(posedge behavioral_mu_ifc.clk);
                Behavioral_MU_write_to_cgra();
                mu2cgra_end_time = $realtime;
            end
        end

        // FORK BRANCH 2: G2F/F2G interrupts (GLB writes data to CGRA and vice-versa)
        begin
            // Wait for an interrupt to tell us when input streaming is done
            // Then wait until interrupt mask contains ALL TILES listed in tile_mask
            // Then clear the interrupt(s)

            // Skip waiting for the G2F interrupt if this is a MU-input-only kernel
            if (kernel.app_type != MU2CGRA) begin
                glb_ctrl = GLB_STRM_G2F_CTRL;
                build_input_tile_mask();
                Env_wait_interrupt();
                Env_clear_interrupt();
                g2f_end_time = $realtime;
                $display("[%s] GLB-to-CGRA streaming done at %0t", kernel.name, g2f_end_time);
            end

            // Wait for an interrupt to tell us when output streaming is done
            // Then wait until interrupt mask contains ALL TILES listed in tile_mask
            // Then clear the interrupt(s)

            glb_ctrl = GLB_STRM_F2G_CTRL;  // 0x30
            build_output_tile_mask();
            Env_wait_interrupt();
            Env_clear_interrupt();
            end_time = $realtime;
            $display("[%s] It takes %0t total time to run kernel.", kernel.name, end_time - start_time);

            total_output_size = 0;
            foreach (kernel.output_size[i]) begin
                total_output_size += kernel.output_size[i];
            end
            $display("[%s] The size of output is %0d Byte.", kernel.name, total_output_size);

            if (kernel.app_type == MU2CGRA) begin
                latency = end_time - mu2cgra_end_time;
                $display("[%s] The initial latency is %0t.", kernel.name, latency);
                $display("[%s] The throughput is %.3f (GB/s).", kernel.name,
                        total_output_size / (mu2cgra_end_time - start_time));
            end else begin
                latency = end_time - g2f_end_time;
                $display("[%s] The initial latency is %0t.", kernel.name, latency);
                $display("[%s] The throughput is %.3f (GB/s).", kernel.name,
                        total_output_size / (g2f_end_time - start_time));
            end
        end

    join

endtask

// For reference: register defs copied from file glc.svh
//  `define GLC_PAR_CFG_G2F_ISR_R 'h38
//  `define GLC_STRM_G2F_ISR_R    'h34
//  `define GLC_STRM_F2G_ISR_R    'h30
//  `define GLC_GLOBAL_ISR_R      'h3c

string reg_name;
task Env_wait_interrupt();

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
                one_cy_delay_if_verilator();  // Vvverilator is off by 1cy here vs. vcs

                // Got an interrupt. One or more tiles have finished streaming.
                // Read the interrupt register to see which one(s) have finished so far.

                AxilDriver_read();
                if (data == 0) begin
                    $display("WARNING: got interrupt, but not from %s", reg_name);
                    continue;  // Keep waiting for the RIGHT interrupt
                end
                // Don't stop until interrupt mask (data) contains ALL tiles in tile_mask
                if (data == tile_mask) break;
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
    $display("%s clear interrupt using mask", reg_name, tile_mask);

    AxilDriver_write();  // Writes to interrupt reg addr from above
endtask // Env_clear_interrupt


task Env_set_interrupt_on();
    $display("Turn on interrupt enable registers");
    addr = `GLC_GLOBAL_IER_R;      data = 3'b111; AxilDriver_write();
    addr = `GLC_PAR_CFG_G2F_IER_R; data =   1'b1; AxilDriver_write();

    // G2F interrupt enable for relevant GLB tiles
    addr = `GLC_STRM_G2F_IER_R;
    data = 32'b0;
    foreach (kernel.inputs[i]) begin
        foreach (kernel.inputs[i].io_tiles[j]) begin
            data |= 1 << kernel.inputs[i].io_tiles[j].tile;
        end
    end
    $display("G2F interrupt enable : %0x\n", data);
    AxilDriver_write();


    // F2G interrupt enable for relevant GLB tiles
    addr = `GLC_STRM_F2G_IER_R;
    data = 32'b0;
    foreach (kernel.outputs[i]) begin
        foreach (kernel.outputs[i].io_tiles[j]) begin
            data |= 1 << kernel.outputs[i].io_tiles[j].tile;
        end
    end
    $display("F2G interrupt enable : %0x\n", data);
    AxilDriver_write();
endtask


task Env_write_network_data();
    realtime start_time, end_time;
    $timeformat(-9, 2, " ns", 0);
    repeat (10) @(posedge p_ifc.clk);
    start_time = $realtime;
    $display("[%s] write network params to glb start at %0t", kernel.name, start_time);

    // inputActivation (INT8)
    start_addr = dnn_layer.inputActivation_start_addr;
    data_q_8b = dnn_layer.inputActivation;
    ProcDriver_write_8b_network_data();

    // inputScale (E8M0)
    start_addr = dnn_layer.inputScale_start_addr;
    data_q_8b = dnn_layer.inputScale;
    ProcDriver_write_8b_network_data();

    // weight INT8
    start_addr = dnn_layer.weight_start_addr;
    data_q_8b = dnn_layer.weight;
    ProcDriver_write_8b_network_data();

    // weightScale (E8M0)
    start_addr = dnn_layer.weightScale_start_addr;
    data_q_8b = dnn_layer.weightScale;
    ProcDriver_write_8b_network_data();

    // bias (bFloat16)
    start_addr = dnn_layer.bias_start_addr;
    data_q_16b = dnn_layer.bias;
    ProcDriver_write_16b_network_data();

    end_time = $realtime;
    $display("[%s] write network params to glb end at %0t", kernel.name, end_time);
    $display("[%s] It takes %0t time to write network params to glb.", kernel.name, end_time - start_time);


endtask // Env_write_network_data


task Env_run();
    // int dpr;  (declared in garnet_test.sv, which "include"s this file)
    // wait for reset
    $display("[%0t] wait for reset", $time);  // 100ps
    repeat (20) @(posedge p_ifc.clk);

    // // turn on interrupt
    // $display("[%0t] turn on interrupt", $time);  // 120ps?
    // Env_set_interrupt_on();

    if (dpr) begin
        $display("ERROR we no longer support dpr TRUE; we're not even sure when/if it was ever used");
        $finish(2);
    end else begin
        $display("\n[%0t] dpr FALSE\n", $time);
        foreach (kernels[i]) begin
            automatic int j = i;
            begin
                $display("[%0t] Processing kernel %0d BEGIN", $time, j);
                kernel = kernels[j];
                 // turn on interrupt
                $display("[%0t] turn on interrupt", $time);  // 120ps?
                Env_set_interrupt_on();
                Env_write_bs();

                if (external_mu_active) begin
                    Env_write_network_data();
                end

                Env_glb_configure();
                Env_cgra_configure();
                Env_write_data();

                // TODO: Think about the order of all these. Make sure MU doesn't start producing valid data until cgra has been unstalled and flushed
                if (external_mu_active) begin
                    Env_mu_configure();
                end

                Env_kernel_test();
                Env_read_data();      $display("[%0t] read_data DONE", $time);
                kernel.compare();
                $display("[%0t] Processing kernel %0d END", $time, j);
            end
        end
    end

endtask // Env_run

task build_input_tile_mask();
    // Build a mask that shows which tiles are receiving data from GLB
    tile_mask = 0;
    foreach (kernel.inputs[i]) begin
        foreach (kernel.inputs[i].io_tiles[j]) begin
            tile_mask |= 1 << kernel.inputs[i].io_tiles[j].tile;
        end
    end
    $display("\n[%0t] Built a INPUT tile mask %0x", $time, tile_mask);
endtask

task build_output_tile_mask();
    // Build a mask that shows which tiles are sending data to GLB
    tile_mask = 0;
    foreach (kernel.outputs[i]) begin
        foreach (kernel.outputs[i].io_tiles[j]) begin
            tile_mask |= 1 << kernel.outputs[i].io_tiles[j].tile;
        end
    end
    $display("\n[%0t] Built a OUTPUT tile mask %0x", $time, tile_mask);
endtask


/* Unused?
task Environment::compare();
    repeat (20) @(vifc_axil.cbd);
    foreach (kernels[i]) begin
        kernels[i].compare();
    end
endtask
*/
