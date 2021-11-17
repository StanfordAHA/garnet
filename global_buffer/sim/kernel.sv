typedef enum int {
    WR,
    RD,
    G2F,
    F2G
} stream_type;

typedef logic [CGRA_DATA_WIDTH-1:0] data16[];
typedef logic [BANK_DATA_WIDTH-1:0] data64[];

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
    data16 data_arr;
    data16 data_arr_out;
    data64 data64_arr;
    data64 data64_arr_out;
endclass