module glb_write #(
    parameter TX_SIZE = 32
    // parameter DATA_FILE = "generic_memory.txt"
)
(
    input logic clk,
    input logic rst_n,
    output logic [15:0] data,
    input logic ready,
    output logic valid,
    output logic done,
    input logic flush
);

logic [15:0] local_mem [0:1023];
integer num_tx;

initial $readmemh("/home/max/Documents/SPARSE/garnet/generic_memory.txt", local_mem);

initial begin
    
    num_tx = 0;
    valid = 0;
    done = 0;
    data = 0;

    @(posedge flush);

    // Make as many transfers from the memory as needed.
    while(num_tx < TX_SIZE) begin
        @(posedge clk);
        data = local_mem[num_tx];
        valid = 1;
        if(ready == 1 && valid == 1) begin
            num_tx = num_tx + 1;
        end
    end
    @(posedge clk);
    done = 1;

end

endmodule