module glb_read #(
    parameter NUM_BLOCKS = 1,
    parameter FILE_NAME1 = "generic_file_0.txt",
    parameter FILE_NAME2 = "generic_file_1.txt",
    parameter LOCATION = "X00_Y00"
    // parameter DATA_FILE0 = "generic_memory_0.txt",
    // parameter DATA_FILE1 = "generic_memory_1.txt"
)
(
    input logic clk,
    input logic rst_n,
    input logic [16:0] data,
    output logic ready,
    input logic valid,
    output logic done,
    input logic flush
);

logic [15:0] local_mem_0 [0:2047];
logic [15:0] local_mem_1 [0:2047];
integer num_rx;
integer size_0;
integer size_1;

string F1_PARGS;
string F2_PARGS;
string NUM_BLOCKS_PARGS;
integer NUM_BLOCKS_USE;
string F1_USE;
string F2_USE;
string ENABLED_PARGS;
integer ENABLED;

initial begin

    ENABLED = 0;
    ENABLED_PARGS = $sformatf("%s_ENABLED=%%d", LOCATION);
    $value$plusargs(ENABLED_PARGS, ENABLED);

    num_rx = 0;
    ready = 0;
    size_0 = 0;
    size_1 = 0;
    done = 0;

    if (ENABLED == 1) begin

        $display("%s is enabled...", LOCATION);

        F1_PARGS = $sformatf("%s_F1=%%s", LOCATION);
        F2_PARGS = $sformatf("%s_F2=%%s", LOCATION);
        NUM_BLOCKS_PARGS = $sformatf("%s_NUM_BLOCKS=%%d", LOCATION);

        $display("Location: %s", LOCATION);
        F1_USE = FILE_NAME1;
        $display("F1_USE before: %s", F1_USE);
        $value$plusargs(F1_PARGS, F1_USE);
        $display("F1_USE after: %s", F1_USE);

        F2_USE = FILE_NAME2;
        $value$plusargs(F2_PARGS, F2_USE);

        NUM_BLOCKS_USE = NUM_BLOCKS;
        $value$plusargs(NUM_BLOCKS_PARGS, NUM_BLOCKS_USE);

        @(posedge flush);
        @(negedge flush);

        @(posedge clk);
        @(posedge clk);
        @(posedge clk);

        // // Wait...
        // repeat (500) begin
        //     @(posedge clk);
        // end

        // Do first transfer...
        while(1) begin
            @(posedge clk);
            // Randomzie ready for backpressure
            #1
            // ready = $urandom();
            ready = 1;
            if(ready == 1 && valid == 1) begin
                size_0 = data;
                num_rx = 0;
                break;
            end
        end

        while(num_rx < size_0) begin
            @(posedge clk);
            #1
            // ready = $urandom();
            ready = 1;
            if(ready == 1 && valid == 1) begin
                local_mem_0[num_rx] = data;
                num_rx = num_rx + 1;
            end
        end

        @(posedge clk);
        ready = 0;
        $writememh(F1_USE, local_mem_0);

        if(NUM_BLOCKS_USE == 2) begin

            // Do second transfer...
            while(1) begin
                @(posedge clk);
                #1
                // ready = $urandom();
                ready = 1;
                if(ready == 1 && valid == 1) begin
                    size_1 = data;
                    num_rx = 0;
                    break;
                end
            end

            while(num_rx < size_1) begin
                @(posedge clk);
                #1
                // ready = $urandom();
                ready = 1;
                if(ready == 1 && valid == 1) begin
                    local_mem_1[num_rx] = data;
                    num_rx = num_rx + 1;
                end
            end

            @(posedge clk);
            ready = 0;
            $writememh(F2_USE, local_mem_1);

        end

    end

    @(posedge clk);
    ready = 0;
    done = 1;

end

endmodule
