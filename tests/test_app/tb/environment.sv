/*=============================================================================
** Module: environemnet.sv
** Description:
**              program to drive garnet testbench
** Author: Keyi Zhang, Taeyoung Kong
** Change history:  10/25/2020 - Implement the first version
**===========================================================================*/

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
    bit simulation_done = 0;

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
    extern function bit [NUM_CGRA_COLS-1:0] calculate_cgra_stall_mask(int start, int num);
    extern function bit [NUM_GLB_TILES-1:0] calculate_glb_stall_mask(int start, int num);
    extern task cgra_stall(bit [NUM_CGRA_COLS-1:0] stall_mask);
    extern task cgra_unstall(bit [NUM_CGRA_COLS-1:0] stall_mask);
    extern task run();
    extern task compare();
    extern task clear_output_glb(Kernel kernel);
    extern task reset_cgra();
    extern task read_input_data_and_dump_interleaved(Kernel kernel);
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
    $timeformat(-9, 2, " ns");
    repeat (10) @(vifc_proc.cbd);
    start_time = $realtime;
    $display("[%s] write bitstream to glb start at %0t", kernel.name, start_time);
    proc_drv.write_bs(kernel.bs_start_addr, kernel.bitstream_data);
    end_time = $realtime;
    $display("[%s] write bitstream to glb end at %0t", kernel.name, end_time);
    $display("[%s] It takes %0t time to write the bitstream to glb.", kernel.name,
             end_time - start_time);
endtask

task Environment::write_data(Kernel kernel);
    realtime start_time, end_time;
    $timeformat(-9, 2, " ns");
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

    foreach (kernel.outputs[i]) begin
        foreach (kernel.outputs[i].io_tiles[j]) begin
            $display("[%s] read output_%0d_block_%0d from glb start", kernel.name, i, j);
            // FIXME: VCS Q-2020.03 Does not support this yet.
            // "Hierarchical reference to a structure array member connected to task ref-port is not supported"
            // proc_drv.read_data(kernel.outputs[i].io_tiles[j].start_addr,
            //                    kernel.outputs[i].io_tiles[j].io_block_data);

            if (kernel.trunc_size > 0) begin
                $display("[%s] clear last %0d rows and columns of output_%0d_block_%0d", kernel.name, kernel.trunc_size, i, j);
                if (kernel.out_img == 0) begin
                    kernel.out_img = (kernel.in_img - kernel.ksize) / kernel.stride + 1;
                end
                if (kernel.glb_o == 0) begin
                    kernel.glb_o = kernel.unroll;
                end
                if (kernel.n_oc == 0) begin
                    // raise error
                    $error("[%s] n_oc is not set", kernel.name);
                end
                // Note that C should be channel number per GLB tile
                proc_drv.clear_last_rows_and_columns(
                    kernel.outputs[i].io_tiles[j].start_addr,
                    kernel.n_oc / kernel.glb_o,
                    kernel.out_img + kernel.pad_o_left + kernel.pad_o_right,
                    kernel.out_img + kernel.pad_o_left + kernel.pad_o_right,
                    kernel.trunc_size
                );
            end

            data_q = new[kernel.outputs[i].io_tiles[j].io_block_data.size()];
            proc_drv.read_data(kernel.outputs[i].io_tiles[j].start_addr, data_q);
            kernel.outputs[i].io_tiles[j].io_block_data = data_q;
            $display("[%s] read output_%0d_block_%0d from glb end", kernel.name, i, j);
        end
    end
endtask

task Environment::read_input_data_and_dump_interleaved(Kernel kernel);
    data_array_t tile_data;
    data_array_t interleaved_data;
    integer file;
    string filename;
    integer i, j, k;
    integer num_elements = 0;
    integer element_count = 0;  // Counter to track elements for line breaks
    integer num_io_tiles;

    repeat (20) @(vifc_proc.cbd);

    // Loop through inputs and interleave data from io_tiles
    foreach (kernel.inputs[i]) begin
        // Generate a unique filename for each input
        filename = $sformatf("%s_input_%0d_data.txt", kernel.name, i);
        $display("[%s] dumping data to file %s", kernel.name, filename);

        file = $fopen(filename, "w");
        if (file == 0) begin
            $error("[%s] Failed to open file %s for writing", kernel.name, filename);
            continue;  // Skip this input if the file cannot be opened
        end

        num_io_tiles = kernel.inputs[i].io_tiles.size();

        // For each io_tile, read the data from memory
        foreach (kernel.inputs[i].io_tiles[j]) begin
            $display("[%s] read input_%0d_block_%0d from glb start", kernel.name, i, j);

            // Read data from the io_tile's start address
            tile_data = new[kernel.inputs[i].io_tiles[j].io_block_data.size()];
            proc_drv.read_data(kernel.inputs[i].io_tiles[j].start_addr, tile_data);
            kernel.inputs[i].io_tiles[j].io_block_data = tile_data;  // Store it in the block

            $display("[%s] read input_%0d_block_%0d from glb end", kernel.name, i, j);
        end

        // Check if there is only one tile; no interleaving required
        if (num_io_tiles == 1) begin
            tile_data = kernel.inputs[i].io_tiles[0].io_block_data;

            // Write data directly for a single tile
            for (k = 0; k < tile_data.size(); k++) begin
                if (element_count % 8 == 7) begin
                    $fwrite(file, "%4h\n", tile_data[k]);  // No space before newline
                end else begin
                    $fwrite(file, "%4h ", tile_data[k]);  // Add space between elements
                end
                element_count += 1;
            end
        end else begin
            // Interleave data from multiple tiles
            num_elements = kernel.inputs[i].io_tiles[0].io_block_data.size();
            interleaved_data = new[num_elements * num_io_tiles];

            // Hacky way to interleave input data
            for (j = 0; j < num_io_tiles; j++) begin
                for (k = 0; k < num_elements; k++) begin
                    interleaved_data[j + num_io_tiles * k] = kernel.inputs[i].io_tiles[j].io_block_data[k];
                end
            end

            // Write interleaved data to the file
            for (k = 0; k < interleaved_data.size(); k++) begin
                if (element_count % 8 == 7) begin
                    $fwrite(file, "%4h\n", interleaved_data[k]);  // No space before newline
                end else begin
                    $fwrite(file, "%4h ", interleaved_data[k]);  // Add space between elements
                end
                element_count += 1;
            end
        end

        // Ensure there's a newline at the end of the file if the last write didn't add one
        if (element_count % 8 != 0) begin
            $fwrite(file, "\n");
        end

        $fclose(file);

        $display("[%s] finished writing input_%0d data", kernel.name, i);
    end
endtask


task Environment::glb_configure(Kernel kernel);
    realtime start_time, end_time;
    $timeformat(-9, 2, " ns");
    start_time = $realtime;
    $display("[%s] glb configuration start at %0t", kernel.name, start_time);
    axil_drv.config_write(kernel.bs_cfg);
    axil_drv.config_write(kernel.kernel_cfg);
    end_time = $realtime;
    $display("[%s] glb configuration end at %0t", kernel.name, end_time);
endtask

task Environment::cgra_configure(Kernel kernel);
    Config cfg;
    int group_start, num_groups;
    bit [NUM_GLB_TILES-1:0] glb_stall_mask;
    bit [NUM_CGRA_COLS-1:0] cgra_stall_mask;

    realtime start_time, end_time;
    $timeformat(-9, 2, " ns");

    group_start = kernel.group_start;
    num_groups = kernel.num_groups;
    glb_stall_mask = calculate_glb_stall_mask(group_start, num_groups);
    cgra_stall_mask = calculate_cgra_stall_mask(group_start, num_groups);

    cgra_stall(cgra_stall_mask);
    start_time = $realtime;
    $display("[%s] fast configuration start at %0t", kernel.name, start_time);
    cfg = kernel.get_pcfg_start_config();
    axil_drv.write(cfg.addr, cfg.data);

    wait_interrupt(GLB_PCFG_CTRL, kernel.bs_tile);
    clear_interrupt(GLB_PCFG_CTRL, kernel.bs_tile);
    end_time = $realtime;
    $display("[%s] fast configuration end at %0t", kernel.name, end_time);
    $display("[%s] It takes %0t time to do parallel configuration.", kernel.name,
             end_time - start_time);

endtask

function bit [NUM_GLB_TILES-1:0] Environment::calculate_glb_stall_mask(int start, int num);
    calculate_glb_stall_mask = '0;
    for (int i = 0; i < num; i++) begin
        calculate_glb_stall_mask |= ((2'b11) << ((start + i) * 2));
    end
endfunction

function bit [NUM_CGRA_COLS-1:0] Environment::calculate_cgra_stall_mask(int start, int num);
    calculate_cgra_stall_mask = '0;
    for (int i = 0; i < num; i++) begin
        calculate_cgra_stall_mask |= ((4'b1111) << ((start + i) * 4));
    end
endfunction

task Environment::cgra_stall(bit [NUM_CGRA_COLS-1:0] stall_mask);
    bit [CGRA_AXI_DATA_WIDTH-1:0] data;
    bit [CGRA_AXI_DATA_WIDTH-1:0] wr_data;

    // Stall CGRA
    axil_drv.read(`GLC_CGRA_STALL_R, data);
    wr_data = stall_mask | data;
    axil_drv.write(`GLC_CGRA_STALL_R, wr_data);

    $display("Stall CGRA with stall mask %8h", stall_mask);
endtask

task Environment::cgra_unstall(bit [NUM_CGRA_COLS-1:0] stall_mask);
    bit [CGRA_AXI_DATA_WIDTH-1:0] data;
    bit [CGRA_AXI_DATA_WIDTH-1:0] wr_data;

    // Unstall CGRA
    axil_drv.read(`GLC_CGRA_STALL_R, data);
    wr_data = (~stall_mask) & data;
    axil_drv.write(`GLC_CGRA_STALL_R, wr_data);

    $display("Unstall CGRA with stall mask %4h", stall_mask);
endtask

task Environment::kernel_test(Kernel kernel);
    Config cfg;
    int total_output_size;
    int group_start, num_groups;
    bit [NUM_GLB_TILES-1:0] glb_stall_mask;
    bit [NUM_CGRA_COLS-1:0] cgra_stall_mask;
    realtime start_time, end_time, g2f_end_time, latency;
    $timeformat(-9, 2, " ns");

    group_start = kernel.group_start;
    num_groups = kernel.num_groups;
    glb_stall_mask = calculate_glb_stall_mask(group_start, num_groups);
    cgra_stall_mask = calculate_cgra_stall_mask(group_start, num_groups);
    cgra_unstall(cgra_stall_mask);

    start_time = $realtime;
    $display("[%s] kernel start at %0t", kernel.name, start_time);
    cfg = kernel.get_strm_start_config();
    axil_drv.write(cfg.addr, cfg.data);

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

task Environment::wait_interrupt(e_glb_ctrl glb_ctrl, bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);
    bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
    bit [CGRA_AXI_DATA_WIDTH-1:0] data;
    string reg_name;

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

    fork
        begin
            forever begin
                // level sensitive interrupt
                wait (top.interrupt);
                axil_drv.read(addr, data);
                if (data[tile_num] == 1) begin
                    $display("%s interrupt from tile %0d", reg_name, tile_num);
                    break;
                end
            end
        end
        begin
            repeat (5_000_000) @(vifc_axil.cbd);
            repeat (1_000_000) @(vifc_axil.cbd);
            $error("@%0t: %m ERROR: Interrupt wait timeout ", $time);
        end
    join_any
    disable fork;
endtask

task Environment::clear_interrupt(e_glb_ctrl glb_ctrl, bit [$clog2(NUM_GLB_TILES)-1:0] tile_num);
    bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
    string reg_name;
    bit [NUM_GLB_TILES-1:0] tile_mask;
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

// Write zeros to the output bank for end-to-end testing
task Environment::clear_output_glb(Kernel kernel);
    int bank_start_addr;
    int zero_array_size;
    data_array_t zero_array;

    if (kernel.num_glb_tiling <= 1) begin
        foreach (kernel.outputs[i]) begin
            foreach (kernel.outputs[i].io_tiles[j]) begin
                $display("[%s] clear output_%0d_block_%0d in GLB Bank before running kernel", kernel.name, i, j);

                bank_start_addr = kernel.outputs[i].io_tiles[j].tile_x << BANK_ADDR_WIDTH;
                $display("[%s] clear output_%0d_block_%0d in GLB Bank start at 0x%0h", kernel.name, i, j, bank_start_addr);

                zero_array_size = 128 * 1024 * 8 / CGRA_DATA_WIDTH;
                $display("[%s] clear output_%0d_block_%0d in GLB Bank size %0d words", kernel.name, i, j, zero_array_size);

                zero_array = new[zero_array_size];
                // Initialize the queue with zeros
                foreach (zero_array[k]) begin
                    zero_array[k] = 0;
                end
                proc_drv.write_data(bank_start_addr, zero_array);
            end
        end
    end else begin
        $display("[%s] GLB tiling is enabled, skip clearing the output GLB Tile", kernel.name);
        $display("[%s] This means padding should not be used when GLB tiling is enabled", kernel.name);
    end
endtask

// Task to reset CGRA between kernels
task Environment::reset_cgra();
    proc_drv.reset_cgra();
endtask

task Environment::run();
    // wait for reset
    repeat (20) @(vifc_proc.cbd);

    // turn on interrupt
    set_interrupt_on();

    if (dpr) begin
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
                    reset_cgra(); // Reset CGRA before starting the kernel
                    set_interrupt_on(); // Re-enable interrupts after reset
                    write_bs(kernels[j]);
                    glb_configure(kernels[j]);
                    cgra_configure(kernels[j]);
                    write_data(kernels[j]);
                    // read_input_data_and_dump_interleaved(kernels[j]);
                    clear_output_glb(kernels[j]);
                    kernel_test(kernels[j]);
                    read_data(kernels[j]);
                    kernels[j].compare();
                end
        end
    end

    simulation_done = 1;
    $display("Simulation done");

endtask

task Environment::compare();
    repeat (20) @(vifc_axil.cbd);
    foreach (kernels[i]) begin
        kernels[i].compare();
    end
endtask
