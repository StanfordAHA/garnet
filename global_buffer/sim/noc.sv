class noc_fm;
    logic [NUM_PRR_WIDTH-1:0] configuration [NUM_PRR];

    extern function configure(bit [NUM_PRR_WIDTH-1:0] configuration [NUM_PRR]);
    extern function update(logic io1_io2f [NUM_PRR], logic [15:0] io16_io2f [NUM_PRR],
                           ref logic io1_f2io [NUM_PRR], ref logic [15:0] io16_f2io [NUM_PRR]);
endclass

function noc_fm::configure(bit [NUM_PRR_WIDTH-1:0] configuration [NUM_PRR]);
    this.configuration = configuration;
endfunction

function noc_fm::update(logic io1_io2f [NUM_PRR], logic [15:0] io16_io2f [NUM_PRR],
                             ref logic io1_f2io [NUM_PRR], ref logic [15:0] io16_f2io [NUM_PRR]);
    for (int i=0; i<NUM_PRR; i++) begin
        io1_f2io[i] = io1_io2f[this.configuration[i]];
        io16_f2io[i] = io16_io2f[this.configuration[i]];
    end
endfunction

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
    if (reset) begin
        for (int i=0; i<NUM_PRR; i++) begin
            io1_f2io[i] <= 0;
            io16_f2io[i] <= 0;
        end
    end else begin
        noc_inst.update(io1_io2f, io16_io2f, io1_f2io, io16_f2io);
    end
end

endmodule

