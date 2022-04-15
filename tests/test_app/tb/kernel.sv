/*=============================================================================
** Module: kernel.sv
** Description:
**              kernel class
** Author: Taeyoung Kong
** Change history:
**  10/25/2020 - Implement the first version
**  06/20/2021 - Implement the second version
**===========================================================================*/

import "DPI-C" function chandle parse_metadata(string filename);
import "DPI-C" function chandle get_place_info(chandle info);
import "DPI-C" function chandle get_bs_info(chandle info);
import "DPI-C" function chandle get_input_info(
    chandle info,
    int index
);
import "DPI-C" function chandle get_output_info(
    chandle info,
    int index
);
import "DPI-C" function int glb_map(chandle kernel);
import "DPI-C" function int get_num_groups(chandle info);
import "DPI-C" function int get_group_start(chandle info);
import "DPI-C" function int get_num_inputs(chandle info);
import "DPI-C" function int get_num_io_tiles(
    chandle info,
    int index
);
import "DPI-C" function int get_num_outputs(chandle info);
import "DPI-C" function string get_placement_filename(chandle info);
import "DPI-C" function string get_bitstream_filename(chandle info);
import "DPI-C" function string get_input_filename(
    chandle info,
    int index
);
import "DPI-C" function string get_output_filename(
    chandle info,
    int index
);
import "DPI-C" function int get_input_size(
    chandle info,
    int index
);
import "DPI-C" function int get_output_size(
    chandle info,
    int index
);
import "DPI-C" function int get_bs_size(chandle info);
import "DPI-C" function int get_bs_tile(chandle info);
import "DPI-C" function int get_bs_start_addr(chandle info);
import "DPI-C" function int get_io_tile_start_addr(
    chandle info,
    int index
);
import "DPI-C" function int get_io_tile_map_tile(
    chandle info,
    int index
);
import "DPI-C" function int get_io_tile_loop_dim(
    chandle info,
    int index
);
import "DPI-C" function int get_io_tile_extent(
    chandle info,
    int index,
    int extent_idx
);
import "DPI-C" function int get_io_tile_data_stride(
    chandle info,
    int index,
    int stride_idx
);
import "DPI-C" function int get_io_tile_cycle_stride(
    chandle info,
    int index,
    int stride_idx
);
import "DPI-C" function chandle get_kernel_configuration(chandle info);
import "DPI-C" function chandle get_pcfg_configuration(chandle info);
import "DPI-C" function int get_configuration_size(chandle info);
import "DPI-C" function int get_configuration_addr(
    chandle info,
    int index
);
import "DPI-C" function int get_configuration_data(
    chandle info,
    int index
);
import "DPI-C" function int get_pcfg_pulse_addr();
import "DPI-C" function int get_pcfg_pulse_data(chandle info);
import "DPI-C" function int get_strm_pulse_addr();
import "DPI-C" function int get_strm_pulse_data(chandle info);

typedef enum int {
    IDLE = 0,
    QUEUED = 1,
    CONFIG = 2,
    RUNNING = 3,
    FINISH = 4
} app_state_t;

typedef struct packed {
    int unsigned addr;
    int unsigned data;
} bitstream_entry_t;

typedef struct {
    bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
    bit [CGRA_AXI_DATA_WIDTH-1:0] data;
} Config;

typedef bit [15:0] data_array_t[];
typedef bitstream_entry_t bitstream_t[];

typedef struct {
    int tile;
    int start_addr;
    int num_data;
    data_array_t io_block_data;
} IOTile;

typedef struct {
    int num_io_tiles;
    IOTile io_tiles[];
} IO;

class Kernel;
    static int cnt = 0;
    // name stores the index and the name of Kernel
    string name;

    chandle kernel_info, bs_info;

    string placement_filename;
    string bitstream_filename;

    int num_groups;
    int group_start;
    int num_inputs;
    int num_outputs;

    // TODO: Put all these into IO inputs/outputs
    // input/output information for testing
    string input_filenames[];
    string output_filenames[];
    int input_size[];
    int output_size[];
    // queue to store data
    data_array_t input_data[];
    data_array_t output_data[];
    data_array_t gold_data[];

    // IO information
    IO inputs[];
    IO outputs[];

    // queue to store bitstream
    bitstream_t bitstream_data;
    int bs_start_addr;
    int bs_size;
    int bs_tile;

    // app state
    app_state_t app_state;

    // configuration
    Config kernel_cfg[];
    Config bs_cfg[];

    extern function new(string app_dir);
    extern function void display();
    extern function data_array_t parse_input_data(int idx);
    extern function data_array_t parse_gold_data(int idx);
    extern function bitstream_t parse_bitstream();
    extern function void add_offset_bitstream(ref bitstream_t bitstream_data, input int offset);
    extern function void print_input(int idx);
    extern function void print_input_block(int idx, int block_idx);
    extern function void print_output(int idx);
    extern function void print_output_block(int idx, int block_idx);
    extern function void print_gold(int idx);
    extern function void print_bitstream();
    extern function void compare();
    extern function int compare_(int idx);
    extern function void assert_(bit cond, string msg);
    extern function int kernel_map();
    extern function Config get_pcfg_start_config();
    extern function Config get_strm_start_config();
endclass

function Kernel::new(string app_dir);
    string app_name, meta_filename;
    int last_str_idx;
    chandle io_info;
    int num_io_tiles;
    int num_pixels;
    int loop_dim;

    last_str_idx = app_dir.getc(app_dir.len() - 1) == "/" ? app_dir.len() - 2 : app_dir.len() - 1;
    for (int i = app_dir.len() - 1; i >= 0; i--) begin
        if (app_dir.getc(i) == "/" && i != (app_dir.len() - 1)) begin
            app_name = app_dir.substr(i + 1, last_str_idx);
            break;
        end
    end
    if (app_name.len() == 0) app_name = app_dir;

    // meta file name is design_meat.json
    meta_filename = {app_dir, "/bin/", "design_meta.json"};
    $sformat(name, "APP%0d-%0s", cnt++, app_name);
    $display("[%s]Initilizing the APP Done", name);

    app_state   = IDLE;

    kernel_info = parse_metadata(meta_filename);
    $display("[%s] Parsing the metadata done", name);
    assert_(kernel_info != null, $sformatf("Unable to find %s", meta_filename));

    bitstream_filename = get_bitstream_filename(kernel_info);
    bs_info = get_bs_info(kernel_info);
    assert_(bs_info != null, $sformatf("Unable to find %s", bitstream_filename));

    num_inputs  = get_num_inputs(kernel_info);
    num_outputs = get_num_outputs(kernel_info);
    num_groups  = get_num_groups(kernel_info);

    $display("[%s] num_inputs: %0d", name, num_inputs);
    $display("[%s] num_outputs: %0d", name, num_outputs);
    $display("[%s] num_groups: %0d", name, num_groups);

    // IO instantiate
    inputs = new[num_inputs];
    outputs = new[num_outputs];
    input_filenames = new[num_inputs];
    input_data = new[num_inputs];
    input_size = new[num_inputs];
    output_filenames = new[num_outputs];
    output_data = new[num_outputs];
    output_size = new[num_outputs];
    gold_data = new[num_outputs];

    for (int i = 0; i < num_inputs; i++) begin
        input_filenames[i] = get_input_filename(kernel_info, i);

        input_size[i] = get_input_size(kernel_info, i);

        input_data[i] = parse_input_data(i);
        $display("Parse input_%0d data Done", i);

        io_info = get_input_info(kernel_info, i);

        num_io_tiles = get_num_io_tiles(io_info, i);
        inputs[i].num_io_tiles = num_io_tiles;
        inputs[i].io_tiles = new[num_io_tiles];

        $display("input_%0d has %0d input blocks", i, num_io_tiles);

        if (num_io_tiles == 1) begin
            inputs[i].io_tiles[0].num_data = input_data[i].size;
            inputs[i].io_tiles[0].io_block_data = input_data[i];
        end else begin
            for (int j = 0; j < num_io_tiles; j++) begin
                num_pixels = input_data[i].size / num_io_tiles;
                inputs[i].io_tiles[j].num_data = num_pixels;
                inputs[i].io_tiles[j].io_block_data = new[num_pixels];
                // NOTE: We assume only innermost loop is unrolled.
                for (int k = 0; k < num_pixels; k++) begin
                    inputs[i].io_tiles[j].io_block_data[k] = input_data[i][j+num_io_tiles*k];
                end
            end
        end
    end

    for (int i = 0; i < num_outputs; i++) begin
        output_filenames[i] = get_output_filename(kernel_info, i);
        output_size[i] = get_output_size(kernel_info, i);
        // convert byte size to 16bit size
        output_data[i] = new[(output_size[i] >> 1)];

        io_info = get_output_info(kernel_info, i);
        num_io_tiles = get_num_io_tiles(io_info, i);
        outputs[i].num_io_tiles = num_io_tiles;
        outputs[i].io_tiles = new[num_io_tiles];

        for (int j = 0; j < num_io_tiles; j++) begin
            loop_dim = get_io_tile_loop_dim(io_info, j);
            for (int k = 0; k < loop_dim; k++) begin
                if (k == 0) begin
                    num_pixels = get_io_tile_extent(io_info, j, k);
                end else begin
                    num_pixels = num_pixels * get_io_tile_extent(io_info, j, k);
                end
            end
            outputs[i].io_tiles[j].io_block_data = new[num_pixels];
        end
    end

    // parse gold data
    for (int i = 0; i < num_outputs; i++) begin
        gold_data[i] = parse_gold_data(i);
    end

    bs_size = get_bs_size(bs_info);
    bitstream_data = parse_bitstream();
endfunction

function bitstream_t Kernel::parse_bitstream();
    int i = 0;
    bitstream_t result = new[bs_size];

    int fp = $fopen(bitstream_filename, "r");
    assert_(fp != 0, "Unable to read bitstream file");
    while (!$feof(
        fp
    )) begin
        int unsigned addr;
        int unsigned data;
        int code;
        bitstream_entry_t entry;
        code = $fscanf(fp, "%08x %08x", entry.addr, entry.data);
        if (code == -1) continue;
        assert_(code == 2, $sformatf(
                "Incorrect bs format. Expected 2 entries, got: %0d. Current entires: %0d",
                code,
                result.size()
                ));
        result[i++] = entry;
    end
    return result;
endfunction

function data_array_t Kernel::parse_input_data(int idx);
    int num_pixel = (input_size[idx] >> 1);  // Pixel is 2byte (16bit) size
    data_array_t result = new[num_pixel];
    // FIXME: VCS does not support to read input to dynamic memory
    // Use temporary register
    bit [15:0] result_tmp[2048*1440-1:0];

    int fp = $fopen(input_filenames[idx], "rb");
    int name_len = input_filenames[idx].len();
    string tmp;
    int cnt;
    int f_out;
    $display("Reading input data %s", input_filenames[idx]);
    assert_(fp != 0, "Unable to read input file");
    if (input_filenames[idx].substr(name_len - 3, name_len - 1) == "pgm") begin
        // just skip the first three lines
        for (int i = 0; i < 3; i++) begin
            f_out = $fgets(tmp, fp);
        end
    end
    if (input_filenames[idx].substr(
            name_len - 3, name_len - 1
        ) == "pgm" | input_filenames[idx].substr(
            name_len - 3, name_len - 1
        ) == "raw") begin
        cnt = $fread(result_tmp, fp);
        foreach (result[i]) begin
            result[i] = result_tmp[i];
        end
    end else begin
        cnt = 0;
        while ($fscanf(
            fp, "%h\n", result[cnt]
        ) == 1) begin
            cnt = cnt + 1;
        end
        // The total size in byte is the number of pixels times 2
        cnt = cnt * 2;
    end
    assert_(cnt == input_size[idx], $sformatf(
            "Unable to read input data. Parsed size is %0d, while expected size is %0d\n",
            cnt,
            input_size[idx]
            ));
    $fclose(fp);
    return result;
endfunction

function data_array_t Kernel::parse_gold_data(int idx);
    int num_pixel = (output_size[idx] >> 1);  // Pixel is 2byte (16bit) size
    data_array_t result = new[num_pixel];
    // FIXME: VCS does not support to read input to dynamic memory
    // Use temporary register
    bit [15:0] result_tmp[2048*1440-1:0];
    int fp = $fopen(output_filenames[idx], "rb");
    int name_len = output_filenames[idx].len();
    string tmp;
    int cnt;
    int f_out;
    assert_(fp != 0, "Unable to read output file");
    if (output_filenames[idx].substr(name_len - 3, name_len - 1) == "pgm") begin
        // just skip the first three lines
        for (int i = 0; i < 3; i++) begin
            f_out = $fgets(tmp, fp);
        end
    end
    if (output_filenames[idx].substr(
            name_len - 3, name_len - 1
        ) == "pgm" | output_filenames[idx].substr(
            name_len - 3, name_len - 1
        ) == "raw") begin
        cnt = $fread(result_tmp, fp);
        foreach (result[i]) begin
            result[i] = result_tmp[i];
        end
    end else begin
        cnt = 0;
        while ($fscanf(
            fp, "%h\n", result[cnt]
        ) == 1) begin
            cnt = cnt + 1;
        end
        // The total size in byte is the number of pixels times 2
        cnt = cnt * 2;
    end
    assert_(cnt == output_size[idx], $sformatf(
            "Unable to read output data. Parsed size is %d, while expected size is %d\n",
            cnt,
            output_size[idx]
            ));
    $fclose(fp);
    return result;
endfunction

function int Kernel::kernel_map();
    chandle cfg;
    chandle io_info;
    int size;

    int result = glb_map(kernel_info);
    if (result == 0) begin
        $display("[%s] glb mapping failed", name);
        return result;
    end

    // update group_start offset and add offset
    group_start = get_group_start(kernel_info);

    // TODO: This should be done at the hardware later
    add_offset_bitstream(bitstream_data, group_start * 4);

    // Set start address after mapping
    bs_start_addr = get_bs_start_addr(bs_info);
    bs_tile = get_bs_tile(bs_info);

    for (int i = 0; i < num_inputs; i++) begin
        io_info = get_input_info(kernel_info, i);
        for (int j = 0; j < inputs[i].num_io_tiles; j++) begin
            inputs[i].io_tiles[j].tile = get_io_tile_map_tile(io_info, j);
            inputs[i].io_tiles[j].start_addr = get_io_tile_start_addr(io_info, j);
        end
    end

    for (int i = 0; i < num_outputs; i++) begin
        io_info = get_output_info(kernel_info, i);
        for (int j = 0; j < outputs[i].num_io_tiles; j++) begin
            outputs[i].io_tiles[j].tile = get_io_tile_map_tile(io_info, j);
            outputs[i].io_tiles[j].start_addr = get_io_tile_start_addr(io_info, j);
        end
    end

    // set configurations
    // bs configuration
    cfg = get_pcfg_configuration(bs_info);
    size = get_configuration_size(cfg);
    bs_cfg = new[size];
    for (int i = 0; i < size; i++) begin
        bs_cfg[i].addr = get_configuration_addr(cfg, i);
        bs_cfg[i].data = get_configuration_data(cfg, i);
    end

    // kernel configuration
    cfg = get_kernel_configuration(kernel_info);
    size = get_configuration_size(cfg);
    kernel_cfg = new[size];
    for (int i = 0; i < size; i++) begin
        kernel_cfg[i].addr = get_configuration_addr(cfg, i);
        kernel_cfg[i].data = get_configuration_data(cfg, i);
    end

    $display("[%s] glb mapping success", name);
    return result;
endfunction

function void Kernel::add_offset_bitstream(ref bitstream_t bitstream_data, input int offset);
    int addr, new_addr;
    bit [7:0] x_coor;
    foreach (bitstream_data[i]) begin
        addr = bitstream_data[i].addr;
        x_coor = (((addr & 32'h0000FF00) >> 8) + offset);
        new_addr = {addr[31:16], x_coor, addr[7:0]};
        bitstream_data[i].addr = new_addr;
    end
endfunction

function Config Kernel::get_pcfg_start_config();
    Config cfg;
    cfg.addr = get_pcfg_pulse_addr();
    cfg.data = get_pcfg_pulse_data(bs_info);
    return cfg;
endfunction

function Config Kernel::get_strm_start_config();
    Config cfg;
    cfg.addr = get_strm_pulse_addr();
    cfg.data = get_strm_pulse_data(kernel_info);
    return cfg;
endfunction

// assertion
function void Kernel::assert_(bit cond, string msg);
    assert (cond)
    else begin
        $display("%s", msg);
        $stacktrace;
        $finish(1);
    end
endfunction

function void Kernel::display();
    $display("Kernel name: %s", name);
endfunction

function void Kernel::compare();
    int result;
    int num_pixels;
    int num_io_tiles;
    int file_out;
    // Hacky way to interleave output data in io_block to final output
    // TODO: Make interleave and uninterleave as a function
    for (int i = 0; i < num_outputs; i++) begin
        num_io_tiles = outputs[i].num_io_tiles;
        if (num_io_tiles == 1) begin
            output_data[i] = outputs[i].io_tiles[0].io_block_data;
        end else begin
            for (int j = 0; j < num_io_tiles; j++) begin
                num_pixels = outputs[i].io_tiles[j].io_block_data.size;
                for (int k = 0; k < num_pixels; k++) begin
                    output_data[i][j+num_io_tiles*k] = outputs[i].io_tiles[j].io_block_data[k];
                end
            end
        end
    end
    // dump output (Assuming one output)
    file_out = $fopen("output.txt", "w");
    for (int i = 0; i < output_data[0].size(); i++) begin
        if (i % 8 == 7) begin
            $fwrite(file_out, "%4h\n", output_data[0][i]);
        end else begin
            $fwrite(file_out, "%4h ", output_data[0][i]);
        end
    end
    result = 0;
    for (int i = 0; i < num_outputs; i++) begin
        result += compare_(i);
    end
    if (result == 0) begin
        $display("%s passed", name);
    end else begin
        $error("%s failed. %0d number of pixels are different.", name, result);
    end
endfunction

function int Kernel::compare_(int idx);
    int result = 0;
    int max_mismatch = 20;
    assert (gold_data[idx].size() == output_data[idx].size())
    else begin
        $display("[%s]-Output[%0d], gold data size is %0d, output data size is %0d", name, idx,
                 gold_data[idx].size(), output_data[idx].size());
        $finish(2);
    end
    for (int i = 0; i < gold_data[idx].size(); i++) begin
        if (gold_data[idx][i] != output_data[idx][i]) begin
            if (result < max_mismatch) begin
                $display("[%s]-Output[%0d], pixel[%0d] Get %02X but expect %02X", name, idx, i,
                         output_data[idx][i], gold_data[idx][i]);
            end else if (result == max_mismatch) begin
                $display("The number of pixels mismatch is over %0d, so it will not print further.",
                         max_mismatch);
            end
            result += 1;
        end
    end
    return result;
endfunction

function void Kernel::print_input(int idx);
    foreach (input_data[idx][i]) begin
        $write("%02X ", input_data[idx][i]);
    end
    $display("\n");
endfunction

function void Kernel::print_input_block(int idx, int block_idx);
    foreach (inputs[idx].io_tiles[block_idx].io_block_data[i]) begin
        $write("%02X ", inputs[idx].io_tiles[block_idx].io_block_data[i]);
    end
    $display("\n");
endfunction

function void Kernel::print_gold(int idx);
    foreach (gold_data[idx][i]) begin
        $write("%02X ", gold_data[idx][i]);
    end
    $display("\n");
endfunction

function void Kernel::print_output(int idx);
    foreach (output_data[idx][i]) begin
        $write("%02X ", output_data[idx][i]);
    end
    $display("\n\n");
endfunction

function void Kernel::print_output_block(int idx, int block_idx);
    foreach (outputs[idx].io_tiles[block_idx].io_block_data[i]) begin
        $write("%02X ", outputs[idx].io_tiles[block_idx].io_block_data[i]);
    end
    $display("\n");
endfunction

function void Kernel::print_bitstream();
    foreach (bitstream_data[i]) begin
        $display("%16X", bitstream_data[i]);
    end
    $display("\n");
endfunction

