module cgra (
    input  logic                                        clk,
    input  logic                                        reset,
    input  logic [NUM_PRR-1:0]                          stall,
    input  logic [NUM_PRR-1:0]                          cfg_wr_en,
    input  logic [NUM_PRR-1:0][CGRA_CFG_ADDR_WIDTH-1:0] cfg_wr_addr,
    input  logic [NUM_PRR-1:0][CGRA_CFG_DATA_WIDTH-1:0] cfg_wr_data,
    input  logic [NUM_PRR-1:0]                          cfg_rd_en,
    input  logic [NUM_PRR-1:0][CGRA_CFG_ADDR_WIDTH-1:0] cfg_rd_addr,
    output logic [NUM_PRR-1:0][CGRA_CFG_DATA_WIDTH-1:0] cfg_rd_data,
    input  logic [NUM_PRR-1:0]                          io1_g2io,
    input  logic [NUM_PRR-1:0][                   15:0] io16_g2io,
    output logic [NUM_PRR-1:0]                          io1_io2g,
    output logic [NUM_PRR-1:0][                   15:0] io16_io2g
);
    localparam int PRR_CFG_REG_DEPTH = 16;

    // ---------------------------------------
    // Configuration
    // ---------------------------------------
    logic [CGRA_CFG_DATA_WIDTH-1:0] cfg_reg[NUM_PRR][PRR_CFG_REG_DEPTH];
    localparam int CGRA_CFG_PRR_WIDTH = $clog2(PRR_CFG_REG_DEPTH);

    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            for (int i = 0; i < NUM_PRR; i++) begin
                for (int j = 0; j < PRR_CFG_REG_DEPTH; j++) begin
                    cfg_reg[i][j] <= 0;
                end
            end
        end else begin
            for (int i = 0; i < NUM_PRR; i++) begin
                if (cfg_wr_en[i]) begin
                    if (cfg_wr_addr[i][CGRA_CFG_ADDR_WIDTH-1-:NUM_PRR_WIDTH] == i) begin
                        cfg_reg[i][cfg_wr_addr[i][CGRA_CFG_PRR_WIDTH-1:0]] <= cfg_wr_data[i];
                    end
                end
            end
        end
    end

    function automatic bit [CGRA_CFG_DATA_WIDTH-1:0] cfg_read(
        bit [CGRA_CFG_ADDR_WIDTH-1:0] addr);
        int prr_id = addr[CGRA_CFG_ADDR_WIDTH-1-:NUM_PRR_WIDTH];
        cfg_read = cfg_reg[prr_id][addr[CGRA_CFG_PRR_WIDTH-1:0]];
    endfunction

    always_comb begin
        for (int i = 0; i < NUM_PRR; i++) begin
            if (cfg_rd_en[i] && cfg_rd_addr[i][CGRA_CFG_ADDR_WIDTH-1-:NUM_PRR_WIDTH] == i) begin
                cfg_rd_data[i] = cfg_reg[i][cfg_rd_addr[i][CGRA_CFG_PRR_WIDTH-1:0]];
            end else begin
                cfg_rd_data[i] = '0;
            end
        end
    end

    // ---------------------------------------
    // Control
    // ---------------------------------------
    bit [NUM_PRR-1:0] is_glb2prr_on;
    bit [NUM_PRR-1:0] is_prr2glb_on;
    bit [NUM_PRR-1:0] is_prr2glb_done;

    bit [NUM_PRR-1:0][99:0] prr2glb_cnt;
    bit [NUM_PRR-1:0] prr2glb_valid;

    bit [15:0] glb2prr_q[int][$];
    bit [15:0] prr2glb_q[int][$];
    bit [99:0] prr2glb_valid_cnt_q[int][$];

    bit flush;

    // ---------------------------------------
    // Data Queue
    // ---------------------------------------

    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            for (int i = 0; i < NUM_PRR; i++) begin
                glb2prr_q[i] = {};
            end
        end else begin
            for (int i = 0; i < NUM_PRR; i++) begin
                if (flush) begin
                    glb2prr_q[i] = {};
                end else if (!stall[i]) begin
                    if (is_glb2prr_on[i] == 1) begin
                        if (io1_g2io[i] == 1) begin
                            glb2prr_q[i].push_back(io16_g2io[i]);
                        end
                    end
                end
            end
        end
    end

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            for (int i = 0; i < NUM_PRR; i++) begin
                prr2glb_q[i] = {};
                io1_io2g[i]  <= 0;
                io16_io2g[i] <= 0;
            end
        end else begin
            for (int i = 0; i < NUM_PRR; i++) begin
                if (flush) begin
                    prr2glb_q[i] = {};
                end else if (!stall[i]) begin
                    if (prr2glb_valid[i] == 1 && (prr2glb_q[i].size() > 0)) begin
                        io1_io2g[i]  <= 1;
                        io16_io2g[i] <= prr2glb_q[i].pop_front();
                    end else begin
                        io1_io2g[i]  <= 0;
                        io16_io2g[i] <= 0;
                    end
                end
            end
        end
    end

    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            prr2glb_valid <= 0;
            prr2glb_cnt <= 0;
            is_prr2glb_done <= '0;
        end else begin
            for (int i = 0; i < NUM_PRR; i++) begin
                if (flush) begin
                    prr2glb_cnt <= 0;
                    is_prr2glb_done <= '0;
                    prr2glb_valid <= 0;
                end else if (!stall[i]) begin
                    if ((is_prr2glb_on[i] == 1) && (is_prr2glb_done[i] == 0)) begin
                        if (prr2glb_cnt[i] == prr2glb_valid_cnt_q[i][0]) begin
                            prr2glb_valid[i] <= 1;
                            void'(iterate_valid_cnt(i));
                        end else begin
                            prr2glb_valid[i] <= 0;
                        end
                        prr2glb_cnt[i] <= prr2glb_cnt[i] + 1;
                    end else begin
                        prr2glb_valid[i] <= 0;
                    end
                end
            end
        end
    end

    initial begin
        foreach (prr2glb_valid_cnt_q[i]) begin
            prr2glb_valid_cnt_q[i] = {};
        end
    end

    function prr2glb_configure(int prr_id, int dim, int extent[LOOP_LEVEL],
                               int cycle_stride[LOOP_LEVEL]);
        bit [99:0] cnt;
        bit done;
        int i_extent[LOOP_LEVEL];
        prr2glb_valid_cnt_q[prr_id] = {};
        done = 0;
        i_extent = '{LOOP_LEVEL{0}};
        while (1) begin
            cnt = 0;
            for (int i = 0; i < dim; i++) begin
                cnt += i_extent[i] * cycle_stride[i];
            end
            prr2glb_valid_cnt_q[prr_id].push_back(cnt);
            for (int i = 0; i < dim; i++) begin
                i_extent[i] += 1;
                if (i_extent[i] == extent[i]) begin
                    i_extent[i] = 0;
                    if (i == dim - 1) done = 1;
                end else begin
                    break;
                end
            end
            if (done == 1) break;
        end
    endfunction

    function glb2prr_on(int prr_id);
        is_glb2prr_on[prr_id] = '1;
    endfunction

    function glb2prr_off(int prr_id);
        is_glb2prr_on[prr_id] = '0;
    endfunction

    function prr2glb_on(int prr_id);
        is_prr2glb_on[prr_id] = '1;
    endfunction

    function prr2glb_off(int prr_id);
        is_prr2glb_on[prr_id] = '0;
    endfunction

    function iterate_valid_cnt(int prr_id);
        void'(prr2glb_valid_cnt_q[prr_id].pop_front());
        if (prr2glb_valid_cnt_q[prr_id].size() == 0) begin
            is_prr2glb_done[prr_id] = 1;
            // void'(prr2glb_off(prr_id));
        end
    endfunction

    function flush_on();
        flush = 1;
    endfunction

    function flush_off();
        flush = 0;
    endfunction

endmodule
