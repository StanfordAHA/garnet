module glb_write #(
    parameter TX_SIZE = 32,
    parameter FILE_NAME = "/home/max/Documents/SPARSE/garnet/generic_memory_0.txt"
    // parameter DATA_FILE = "generic_memory.txt"
)
(
    input logic clk,
    input logic rst_n,
    output logic [16:0] data,
    input logic ready,
    output logic valid,
    output logic done,
    input logic flush
);

logic [15:0] local_mem [0:2047];
integer num_tx;


initial begin
    // string file_str;
    // file_str = $sformatf("/home/max/Documents/SPARSE/garnet/generic_memory_%d.txt", FILE_NO);
    $readmemh(FILE_NAME, local_mem);
end

initial begin
    
    num_tx = 0;
    valid = 0;
    done = 0;
    data = 0;

    @(posedge flush);
    @(negedge flush);

    @(posedge clk);
    @(posedge clk);
    @(posedge clk);

    // Make as many transfers from the memory as needed.
    while(num_tx < TX_SIZE) begin
        @(posedge clk);
        #1;
        data = local_mem[num_tx];
        valid = 1;
        if(ready == 1 && valid == 1) begin
            num_tx = num_tx + 1;
        end
    end
    @(posedge clk);
    done = 1;
    valid = 0;

end

endmodule