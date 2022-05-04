module glb_read #(
    parameter NUM_BLOCKS = 1;
    parameter DATA_FILE0 = "generic_memory_0.txt";
    parameter DATA_FILE1 = "generic_memory_1.txt";
)
(
    input logic clk,
    input logic rst_n,
    input logic [15:0] data,
    output logic ready,
    input logic valid,
    output logic done
);

logic [15:0] local_mem_0 [0:1023];
logic [15:0] local_mem_1 [0:1023];
integer num_rx;
integer size_0;
integer size_1;

initial begin
    
    num_rx = 0;
    ready = 0;
    size_0 = 0;
    size_1 = 0;

    // Do first transfer...
    while(1) begin
        @(posedge clk);
        ready = 1;
        if(ready == 1 && valid == 1) begin
            size_0 = data;
            num_rx = 0
        end
    end

    while(num_rx < size_0) begin
        @(posedge clk);
        if(ready == 1 && valid == 1) begin
            local_mem_0[num_rx] = data
            num_rx = num_rx + 1;
        end
    end

    @(posedge clk)
    ready = 0;
    $writememh(DATA_FILE0, local_mem_0)

    if(NUM_BLOCKS == 2) begin

        // Do second transfer...
        while(1) begin
            @(posedge clk);
            if(ready == 1 && valid == 1) begin
                size_1 = data;
                num_rx = 0
            end
        end

        while(num_rx < size_1) begin
            @(posedge clk);
            if(ready == 1 && valid == 1) begin
                local_mem_1[num_rx] = data
                num_rx = num_rx + 1;
            end
        end

        $writememh(DATA_FILE1, local_mem_1)

    end

    @(posedge clk)
    ready = 0;
    done = 1;

end

endmodule: glb_write