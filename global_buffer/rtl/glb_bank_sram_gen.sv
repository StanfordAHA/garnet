//Generate to create larger memories from output of 2048x64 sram macro
//Author: Alex Carsello

module glb_bank_sram_gen #(
    parameter integer DATA_WIDTH = 64,
    parameter integer ADDR_WIDTH = 14
)
(A,CEB,BWEB,CLK,WEB,D,Q);
localparam integer WORD_DEPTH = (1 << ADDR_WIDTH);
localparam integer PER_MEM_ADDR_WIDTH = 11;
localparam integer PER_MEM_WORD_DEPTH = (1 << PER_MEM_ADDR_WIDTH);
localparam integer NUM_INST = (WORD_DEPTH + PER_MEM_WORD_DEPTH - 1)/PER_MEM_WORD_DEPTH;

input                           CLK;
input                           CEB;
input                           WEB;
input   [DATA_WIDTH-1:0]        BWEB;
input   [ADDR_WIDTH-1:0]        A;
input   [DATA_WIDTH-1:0]        D;
output  [DATA_WIDTH-1:0]        Q;

//INPUTS
logic [NUM_INST-1:0] WEB_array;
logic [PER_MEM_ADDR_WIDTH-1:0] A_to_mem;

//OUTPUTS
logic [DATA_WIDTH-1:0] Q_array [NUM_INST-1:0];
logic [DATA_WIDTH-1:0] data_out;

//address bits not going directly to SRAMs
logic [ADDR_WIDTH-PER_MEM_ADDR_WIDTH-1:0] mem_select;

logic [ADDR_WIDTH-PER_MEM_ADDR_WIDTH-1:0] output_select;

// Address bits that are not going to each SRAM
// will be used to select which SRAM to read from/write to
assign mem_select = A[ADDR_WIDTH-1:PER_MEM_ADDR_WIDTH];
assign A_to_mem = A[PER_MEM_ADDR_WIDTH-1:0];

//INPUTS
//Decode mem_select to apply control inputs to correct SRAM
assign WEB_array = (~WEB) ? ~(1 << mem_select) : ~0;

//OUTPUTS
assign Q = data_out;
assign data_out = Q_array[output_select];

// pipeline registers
logic                   CEB_d1, CEB_d2;
logic                   WEB_d1, WEB_d2;
logic [DATA_WIDTH-1:0]  BWEB_d1, BWEB_d2;
logic [DATA_WIDTH-1:0]  D_d1, D_d2;
logic [NUM_INST-1:0]    WEB_array_d1, WEB_array_d2;
logic [ADDR_WIDTH-PER_MEM_ADDR_WIDTH-1:0] mem_select_d1, mem_select_d2;
logic [PER_MEM_ADDR_WIDTH-1:0] A_to_mem_d1, A_to_mem_d2;


always_ff @(posedge CLK) begin
    WEB_d1 <= WEB;
    WEB_d2 <= WEB_d1;
end

always_ff @ (posedge CLK) begin
    if (CEB_d2 == 0) begin
        if (WEB_d2 == 1) begin
            output_select <= mem_select_d2;
        end
    end
end

always_ff @(posedge CLK) begin
    mem_select_d1 <= mem_select;
    mem_select_d2 <= mem_select_d1;
end

// pipeline registers
always_ff @(posedge CLK) begin
    D_d1 <= D;
    D_d2 <= D_d1;
end

always_ff @(posedge CLK) begin
    WEB_array_d1 <= WEB_array;
    WEB_array_d2 <= WEB_array_d1;
end

always_ff @(posedge CLK) begin
    A_to_mem_d1 <= A_to_mem;
    A_to_mem_d2 <= A_to_mem_d1;
end

always_ff @(posedge CLK) begin
    CEB_d1 <= CEB;
    CEB_d2 <= CEB_d1;
end

always_ff @(posedge CLK) begin
    BWEB_d1 <= BWEB;
    BWEB_d2 <= BWEB_d1;
end

//Use parameters to decide which width of memory to instantiate and how many
genvar i;
generate
    for (i = 0; i < NUM_INST; i = i + 1) begin
        logic [63:0] Q_temp;
        TS1N16FFCLLSBLVTC2048X64M8SW
        sram_array (.CLK(CLK), .A(A_to_mem_d2), .BWEB(BWEB_d2), .CEB(CEB_d2), .WEB(WEB_array_d2[i]), .D(D_d2), .Q(Q_temp), .RTSEL(2'b01), .WTSEL(2'b00));
        assign Q_array[i] = Q_temp[DATA_WIDTH-1:0];
    end
endgenerate

endmodule

