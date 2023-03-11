module glb_write #(
    parameter TX_SIZE = 32,
    parameter FILE_NAME = "/home/max/Documents/SPARSE/garnet/generic_memory_0.txt",
    parameter LOCATION = "X00_Y00"
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

string TX_SIZE_PARGS;
string FILE_NAME_PARGS;
integer TX_SIZE_USE;
string FILE_NAME_USE;
string ENABLED_PARGS;
integer ENABLED;

initial begin

    num_tx = 0;
    valid = 0;
    done = 0;
    data = 0;
    valid = 0;

    ENABLED = 0;
    ENABLED_PARGS = $sformatf("%s_ENABLED=%%d", LOCATION);
    $value$plusargs(ENABLED_PARGS, ENABLED);

    if (ENABLED == 1) begin

        $display("%s is enabled...", LOCATION);

        FILE_NAME_PARGS = $sformatf("%s_FILE_NAME=%%s", LOCATION);
        FILE_NAME_USE = FILE_NAME;
        $value$plusargs(FILE_NAME_PARGS, FILE_NAME_USE);
        // string file_str;
        // file_str = $sformatf("/home/max/Documents/SPARSE/garnet/generic_memory_%d.txt", FILE_NO);
        $readmemh(FILE_NAME_USE, local_mem);

        TX_SIZE_PARGS = $sformatf("%s_TX_SIZE=%%d", LOCATION);
        TX_SIZE_USE = TX_SIZE;
        $value$plusargs(TX_SIZE_PARGS, TX_SIZE_USE);

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
        while(num_tx < TX_SIZE_USE) begin
            @(posedge clk);
            #1;
            data = local_mem[num_tx];
            valid = 1;
            if(ready == 1 && valid == 1) begin
                num_tx = num_tx + 1;
            end
        end

    end

    @(posedge clk);
    done = 1;
    valid = 0;

end

endmodule