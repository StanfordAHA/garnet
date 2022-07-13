typedef enum int {
    WR   = 0,
    RD   = 1,
    G2F  = 2,
    F2G  = 3,
    PCFG = 4,
    SRAM = 5
} stream_type;

typedef enum int {
    ST_MODE_VALID = ST_DMA_VALID_MODE_VALID,
    ST_MODE_RV = ST_DMA_VALID_MODE_READY_VALID,
    ST_MODE_RVC = ST_DMA_VALID_MODE_READY_VALID_COMPRESSED,
    ST_MODE_STATIC = ST_DMA_VALID_MODE_STATIC
} st_valid_type;

typedef enum int {
    LD_MODE_EF = LD_DMA_VALID_MODE_EXTERNAL_FLUSH,
    LD_MODE_IF = LD_DMA_VALID_MODE_INTERNAL_FLUSH,
    LD_MODE_VALID = LD_DMA_VALID_MODE_VALID,
    LD_MODE_RV = LD_DMA_VALID_MODE_READY_VALID
} ld_valid_type;

typedef logic [CGRA_DATA_WIDTH-1:0] data16[];
typedef logic [BANK_DATA_WIDTH-1:0] data64[];

class Kernel;
    static int cnt = 0;
    stream_type type_;
    st_valid_type st_valid_type_;
    ld_valid_type ld_valid_type_;
    int first_block_size;
    int second_block_size;
    int block_size_q[$];
    int tile_id;
    int bank_id;
    int start_addr;
    int cycle_start_addr;
    int check_tile_id;
    int dim;
    int extent[LOAD_DMA_LOOP_LEVEL];
    int cycle_stride[LOAD_DMA_LOOP_LEVEL];
    int data_stride[LOAD_DMA_LOOP_LEVEL];
    int new_extent[LOAD_DMA_LOOP_LEVEL];
    int new_cycle_stride[LOAD_DMA_LOOP_LEVEL];
    int new_data_stride[LOAD_DMA_LOOP_LEVEL];
    string filename;
    data16 mem;
    data16 data_arr;
    data16 data_arr_out;
    int total_cycle;
    data64 data64_arr;
    data64 data64_arr_out;
endclass

class Test;
    const int tile_offset = 1 << (BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH);
    const int bank_offset = 1 << BANK_ADDR_WIDTH;
    string filename;
    int num_kernels;
    int data_network_mask;
    Kernel kernels[];
    bit [NUM_GLB_TILES-1:0] g2f_tile_mask;
    bit [NUM_GLB_TILES-1:0] f2g_tile_mask;
    bit [NUM_GLB_TILES-1:0] pcfg_tile_mask;
    bit [NUM_GLB_TILES-1:0] pcfg_broadcast_stall_mask;
    bit [`GLB_PCFG_BROADCAST_MUX_R_MSB:0] pcfg_broadcast_mux_value[NUM_GLB_TILES-1:0];

    extern function new(string filename);
endclass

function Test::new(string filename);
    int fd = $fopen(filename, "r");
    string type_, st_valid_type_, ld_valid_type_, data_filename;
    int first_block_size;
    int tile_id, bank_id, dim;
    int tmp_start_addr, tmp_cycle_start_addr;
    string cycle_stride_s, extent_s, data_stride_s, tmp_s;
    string new_cycle_stride_s, new_extent_s, new_data_stride_s, new_tmp_s;
    string line;
    int start_tile, end_tile, tmp_tile;
    int data_cnt;

    $display("\n---- Test Initialization ----");
    if (fd) $display("Test file open %s", filename);
    else $error("Cannot open %s", filename);
    // Skip the first line
    void'($fgets(line, fd));
    $display("[Description] %s", line);
    void'($fscanf(fd, " %d", num_kernels));
    void'($fscanf(fd, " %b", data_network_mask));
    kernels = new[num_kernels];
    for (int i = 0; i < num_kernels; i++) begin
        kernels[i] = new();
        void'($fscanf(
            fd, " %s%d%d%d%d", type_, tile_id, bank_id, tmp_start_addr, tmp_cycle_start_addr
        ));
        if (type_ == "WR") kernels[i].type_ = WR;
        else if (type_ == "RD") kernels[i].type_ = RD;
        else if (type_ == "G2F") kernels[i].type_ = G2F;
        else if (type_ == "F2G") kernels[i].type_ = F2G;
        else if (type_ == "PCFG") kernels[i].type_ = PCFG;
        else if (type_ == "SRAM") kernels[i].type_ = SRAM;
        else $error("This type [%s] is not supported", type_);
        if (type_ == "G2F") begin
            void'($fscanf(fd, " %s", ld_valid_type_));
            if (ld_valid_type_ == "EF") kernels[i].ld_valid_type_ = LD_MODE_EF;
            else if (ld_valid_type_ == "IF") kernels[i].ld_valid_type_ = LD_MODE_IF;
            else if (ld_valid_type_ == "VALID") kernels[i].ld_valid_type_ = LD_MODE_VALID;
            else if (ld_valid_type_ == "RV") kernels[i].ld_valid_type_ = LD_MODE_RV;
            else $error("This type [%s] is not supported", ld_valid_type_);
        end else if (type_ == "F2G") begin
            void'($fscanf(fd, " %s", st_valid_type_));
            if (st_valid_type_ == "VALID") kernels[i].st_valid_type_ = ST_MODE_VALID;
            else if (st_valid_type_ == "RV") kernels[i].st_valid_type_ = ST_MODE_RV;
            else if (st_valid_type_ == "RVC") kernels[i].st_valid_type_ = ST_MODE_RVC;
            else if (st_valid_type_ == "STATIC") kernels[i].st_valid_type_ = ST_MODE_STATIC;
            else $error("This type [%s] is not supported", st_valid_type_);
            if (kernels[i].st_valid_type_ == ST_MODE_RVC) begin
                void'($fscanf(fd, " %d", first_block_size));
                kernels[i].first_block_size = first_block_size;
            end
        end
        void'($fscanf(fd, " %d", dim));
        kernels[i].tile_id = tile_id;
        kernels[i].bank_id = bank_id;
        kernels[i].start_addr = bank_offset * bank_id + tmp_start_addr;
        kernels[i].cycle_start_addr = tmp_cycle_start_addr;
        kernels[i].check_tile_id = tmp_cycle_start_addr;
        kernels[i].dim = dim;
        for (int j = 0; j < dim; j++) begin
            void'($fscanf(fd, " %d", kernels[i].extent[j]));
        end
        for (int j = 0; j < dim; j++) begin
            void'($fscanf(fd, " %d", kernels[i].cycle_stride[j]));
        end
        for (int j = 0; j < dim; j++) begin
            void'($fscanf(fd, " %d", kernels[i].data_stride[j]));
        end
        if (kernels[i].st_valid_type_ == ST_MODE_RVC) begin
            data_cnt = 1;
            for (int j = 0; j < kernels[i].dim; j++) begin
                data_cnt += (kernels[i].extent[j] - 1) * kernels[i].data_stride[j];
            end
            kernels[i].second_block_size = data_cnt - kernels[i].first_block_size;
        end
        void'($fscanf(fd, " %s", data_filename));
        kernels[i].filename = data_filename;

        // Make extent/stride hardware-friendly
        for (int j = 0; j < dim; j++) begin
            kernels[i].new_extent[j] = kernels[i].extent[j] - 2;
            kernels[i].new_cycle_stride[j] = kernels[i].cycle_stride[j];
            kernels[i].new_data_stride[j] = kernels[i].data_stride[j];
            for (int k = 0; k < j; k++) begin
                kernels[i].new_cycle_stride[j] -= kernels[i].cycle_stride[k] * (kernels[i].extent[k] - 1);
                kernels[i].new_data_stride[j]  -= kernels[i].data_stride[k] * (kernels[i].extent[k] - 1);
            end
            kernels[i].new_data_stride[j] = kernels[i].new_data_stride[j] << CGRA_BYTE_OFFSET;
        end
    end
    $fclose(fd);

    for (int i = 0; i < num_kernels; i++) begin
        if (kernels[i].type_ == G2F) g2f_tile_mask[kernels[i].tile_id] = 1;
        else if (kernels[i].type_ == F2G) f2g_tile_mask[kernels[i].tile_id] = 1;
        else if (kernels[i].type_ == PCFG) pcfg_tile_mask[kernels[i].tile_id] = 1;
    end

    // Calculate total cycles
    for (int i = 0; i < num_kernels; i++) begin
        if (kernels[i].type_ == G2F || kernels[i].type_ == F2G) begin
            kernels[i].total_cycle = kernels[i].cycle_stride[kernels[i].dim - 1] * kernels[i].extent[kernels[i].dim - 1] + kernels[i].cycle_start_addr;
        end else if (kernels[i].type_ == PCFG) begin
            kernels[i].total_cycle = kernels[i].extent[0] / 4;
        end
    end

    // Calculate stall
    pcfg_broadcast_stall_mask = {NUM_GLB_TILES{1'b1}};
    for (int i = 0; i < num_kernels; i++) begin
        // For PCFG test, unstall pcfg logic
        if (kernels[i].type_ == PCFG) begin
            pcfg_broadcast_stall_mask = 0;
            break;
        end
    end

    for (int i = 0; i < NUM_GLB_TILES; i++) begin
        pcfg_broadcast_mux_value[i] = 0;
    end
    for (int i = 0; i < num_kernels; i++) begin
        if (kernels[i].type_ == PCFG) begin
            start_tile = kernels[i].tile_id;
            end_tile   = kernels[i].check_tile_id;
            if (start_tile <= end_tile) begin
                pcfg_broadcast_mux_value[start_tile] = (1 << `GLB_PCFG_BROADCAST_MUX_SOUTH_F_LSB) | (1 << `GLB_PCFG_BROADCAST_MUX_EAST_F_LSB) | (0 << `GLB_PCFG_BROADCAST_MUX_WEST_F_LSB);
                for (int j = start_tile + 1; j <= end_tile; j++) begin
                    pcfg_broadcast_mux_value[j] = (2 << `GLB_PCFG_BROADCAST_MUX_SOUTH_F_LSB) | (2 << `GLB_PCFG_BROADCAST_MUX_EAST_F_LSB) | (0 << `GLB_PCFG_BROADCAST_MUX_WEST_F_LSB);
                end
            end else begin
                pcfg_broadcast_mux_value[start_tile] = (1 << `GLB_PCFG_BROADCAST_MUX_SOUTH_F_LSB) | (0 << `GLB_PCFG_BROADCAST_MUX_EAST_F_LSB) | (1 << `GLB_PCFG_BROADCAST_MUX_WEST_F_LSB);
                for (int j = start_tile - 1; j >= end_tile; j--) begin
                    pcfg_broadcast_mux_value[j] = (3 << `GLB_PCFG_BROADCAST_MUX_SOUTH_F_LSB) | (0 << `GLB_PCFG_BROADCAST_MUX_EAST_F_LSB) | (2 << `GLB_PCFG_BROADCAST_MUX_WEST_F_LSB);
                end
            end
        end
    end

    // Display log
    $display("Number of kernels in the app is %0d", num_kernels);
    $display("Data interconnect of app is %16b", data_network_mask);
    foreach (kernels[i]) begin
        extent_s = "";
        cycle_stride_s = "";
        data_stride_s = "";
        new_extent_s = "";
        new_cycle_stride_s = "";
        new_data_stride_s = "";
        $display(
            "Kernel %0d: Type: %s, Tile_ID: %0d, Bank_ID: %0d, Start_addr: %0d, Cycle_start_addr: %0d",
            i, kernels[i].type_.name(), kernels[i].tile_id, kernels[i].bank_id,
            kernels[i].start_addr, kernels[i].cycle_start_addr);
        if (kernels[i].type_ == G2F) begin
            $display("Kernel %0d: Valid Mode: %s", i, kernels[i].ld_valid_type_.name());
        end else if (kernels[i].type_ == F2G) begin
            $display("Kernel %0d: Valid Mode: %s", i, kernels[i].st_valid_type_.name());
            if (kernels[i].st_valid_type_ == ST_MODE_RVC) begin
                $display("First Block size: %0d", kernels[i].first_block_size);
                $display("Second Block size: %0d", kernels[i].second_block_size);
            end
        end
        for (int j = 0; j < kernels[i].dim; j++) begin
            tmp_s.itoa(kernels[i].extent[j]);
            new_tmp_s.itoa(kernels[i].new_extent[j]);
            extent_s = {extent_s, " ", tmp_s};
            new_extent_s = {new_extent_s, " ", new_tmp_s};

            tmp_s.itoa(kernels[i].cycle_stride[j]);
            new_tmp_s.itoa(kernels[i].new_cycle_stride[j]);
            cycle_stride_s = {cycle_stride_s, " ", tmp_s};
            new_cycle_stride_s = {new_cycle_stride_s, " ", new_tmp_s};

            tmp_s.itoa(kernels[i].data_stride[j]);
            new_tmp_s.itoa(kernels[i].new_data_stride[j]);
            data_stride_s = {data_stride_s, " ", tmp_s};
            new_data_stride_s = {new_data_stride_s, " ", new_tmp_s};
        end
        $display("[BEFORE] Extent: [%s], cycle_stride: [%s], data_stride: [%s]", extent_s,
                 cycle_stride_s, data_stride_s);
        $display("[AFTER] Extent: [%s], cycle_stride: [%s], data_stride: [%s]", new_extent_s,
                 new_cycle_stride_s, new_data_stride_s);
    end
endfunction
