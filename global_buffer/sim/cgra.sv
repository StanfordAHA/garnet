module cgra (
    input  logic                                        clk,
    input  logic                                        reset,
    input  logic [NUM_PRR-1:0]                          stall,
    input  logic [NUM_PRR-1:0]                          cfg_wr_en ,
    input  logic [NUM_PRR-1:0][CGRA_CFG_ADDR_WIDTH-1:0] cfg_wr_addr ,
    input  logic [NUM_PRR-1:0][CGRA_CFG_DATA_WIDTH-1:0] cfg_wr_data ,
    input  logic [NUM_PRR-1:0]                          cfg_rd_en,
    input  logic [NUM_PRR-1:0][CGRA_CFG_ADDR_WIDTH-1:0] cfg_rd_addr,
    output logic [NUM_PRR-1:0][CGRA_CFG_DATA_WIDTH-1:0] cfg_rd_data,
    input  logic [NUM_PRR-1:0]                          io1_g2io,
    input  logic [NUM_PRR-1:0][15:0]                    io16_g2io,
    output logic [NUM_PRR-1:0]                          io1_io2g,
    output logic [NUM_PRR-1:0][15:0]                    io16_io2g
);

localparam int PRR_CFG_REG_DEPTH = 16;

// ---------------------------------------
// Configuration
// ---------------------------------------
logic [CGRA_CFG_DATA_WIDTH-1:0] cfg_reg [NUM_PRR][PRR_CFG_REG_DEPTH];
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
                if (cfg_wr_addr[i][CGRA_CFG_ADDR_WIDTH-1 -: NUM_PRR_WIDTH] == i) begin
                    cfg_reg[i][cfg_wr_addr[i][CGRA_CFG_PRR_WIDTH-1:0]] <= cfg_wr_data[i];
                end
            end
        end
    end
end

always_comb begin
    for (int i = 0; i < NUM_PRR; i++) begin
        if (cfg_rd_en[i] && cfg_rd_addr[i][CGRA_CFG_ADDR_WIDTH-1 -:NUM_PRR_WIDTH] == i) begin
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
bit [15:0] glb2prr_q[int][$];
bit [15:0] prr2glb_q[int][$];

// ---------------------------------------
// Data Queue
// ---------------------------------------

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i = 0; i < NUM_PRR; i++) begin
            glb2prr_q[i] = {};
        end
    end
    else begin
        for (int i = 0; i < NUM_PRR; i++) begin
            if (!stall[i]) begin
                if (is_glb2prr_on[i] == 1) begin
                    if (io1_g2io[i] == 1) begin
                        glb2prr_q[i].push_back(io16_g2io[i]);
                    end
                end
            end
        end
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i = 0; i < NUM_PRR; i++) begin
            prr2glb_q[i] = {};
        end
    end
    else begin
        for (int i = 0; i < NUM_PRR; i++) begin
            if (!stall[i]) begin
                if (is_prr2glb_on[i] == 1 && (prr2glb_q[i].size() > 0)) begin
                    io1_io2g[i] <= 1;
                    io16_io2g[i] <= glb2prr_q[i].pop_front();
                end
                else begin
                    io1_io2g[i] <= 0;
                    io16_io2g[i] <= 0;
                end
            end
        end
    end
end

function glb2prr_on(int prr_id);
    is_glb2prr_on[prr_id] = 1;
endfunction

function glb2prr_off(int prr_id);
    is_glb2prr_on[prr_id] = 0;
endfunction

function prr2glb_on(int prr_id);
    is_prr2glb_on[prr_id] = 1;
endfunction

function prr2glb_off(int prr_id);
    is_prr2glb_on[prr_id] = 0;
endfunction

endmodule
