import header::*;
class noc_fm;
    logic io1_io2f [NUM_PRR];
    logic [15:0] io16_io2f [NUM_PRR];
    logic io1_f2io [NUM_PRR];
    logic [15:0] io16_f2io [NUM_PRR];
    extern function passthrough(logic io1_io2f [NUM_PRR], logic [15:0] io16_io2f [NUM_PRR],
                                ref logic io1_f2io [NUM_PRR], ref logic [15:0] io16_f2io [NUM_PRR]);
endclass

function noc_fm::passthrough(logic io1_io2f [NUM_PRR], logic [15:0] io16_io2f [NUM_PRR],
                             ref logic io1_f2io [NUM_PRR], ref logic [15:0] io16_f2io [NUM_PRR]);
    this.io1_io2f = io1_io2f;
    this.io16_io2f = io16_io2f;
    
    for(int i=0; i < NUM_PRR; i++) begin
        this.io16_f2io[i] = this.io16_io2f[i];
        this.io1_f2io[i] = this.io1_io2f[i];
    end

    io1_f2io = this.io1_f2io;
    io16_f2io = this.io16_f2io;

endfunction

// function noc_fm::configure(bit [NUM_PRR_WIDTH-1:0] configuration [NUM_PRR]);
//     this.
// endfunction

module noc (
    input  logic        clk,
    input  logic        reset,
    input  logic        io1_io2f [NUM_PRR],
    input  logic [15:0] io16_io2f [NUM_PRR],
    output logic        io1_f2io [NUM_PRR],
    output logic [15:0] io16_f2io [NUM_PRR]
);

noc_fm noc_inst;

initial begin
    noc_inst = new();
end

always_ff @(posedge clk or posedge reset) begin
    noc_inst.passthrough(io1_io2f, io16_io2f, io1_f2io, io16_f2io);
end

endmodule

