typedef enum int {
    WR = 0,
    RD = 1,
    G2F = 2,
    F2G = 3
} stream_type;

class Kernel;
    static int cnt = 0;
    stream_type type_;
    int tile_id;
    int start_addr;
    int dim;
    int extent[LOOP_LEVEL];
    int cycle_stride[LOOP_LEVEL];
    int data_stride[LOOP_LEVEL];
    string filename;
    logic [CGRA_DATA_WIDTH-1:0] data_arr[];
    logic [CGRA_DATA_WIDTH-1:0] data_arr_out[];
    logic [BANK_DATA_WIDTH-1:0] data64_arr[];
    logic [BANK_DATA_WIDTH-1:0] data64_arr_out[];
endclass