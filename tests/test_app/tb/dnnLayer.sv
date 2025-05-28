/*=============================================================================
** Module: dnnLayer.sv
** Description:
**              dnnLayer class
** Author: Michael Oduoza
** Change history:
**  04/15/2025 - Implement the first version
**===========================================================================*/



typedef bit [7:0] byte_array_t[];
typedef bit [15:0] half_array_t[];

typedef bit[31:0] matrix_params_array_t[];

class DnnLayer;

    byte_array_t inputActivation;
    byte_array_t weight;
    half_array_t bias;
    byte_array_t inputScale;
    byte_array_t weightScale;
    matrix_params_array_t serialized_matrix_params;

    // Have some metadata to store the shape of each tensor and its resultant total size
    int layer_X;
    int layer_Y;
    int layer_IC;
    int layer_OC;
    int layer_FX;
    int layer_FY;
    int layer_BLOCK_SIZE;

    int inputActivation_size;
    int weight_size;
    int bias_size;
    int inputScale_size;
    int weightScale_size;
    int matrix_params_size;

    // Start addresses must be 32B aligned b/c 32 is the channel unrolling
    real inputActivation_size_aligned;
    real weight_size_aligned;
    real bias_size_aligned;
    real inputScale_size_aligned;
    real weightScale_size_aligned;

    int glb_base_addr;

    int inputActivation_start_addr;
    int weight_start_addr;
    int bias_start_addr;
    int inputScale_start_addr;
    int weightScale_start_addr;

    string inputActivation_filename;
    string weight_filename;
    string bias_filename;
    string inputScale_filename;
    string weightScale_filename;
    string matrix_params_filename;

    extern function new();
    extern function byte_array_t parse_8b_data(string filename, int size);
    extern function half_array_t parse_16b_data(string filename, int size);
    extern function matrix_params_array_t parse_32b_data(string filename, int size);
    extern function void assertion(bit cond, string msg);


endclass



function DnnLayer::new();

   // Hardcoded for now. In the future, these should be set in a more streamlined way
   layer_X = 56;
   layer_Y = 56;
   layer_IC = 64;
   layer_OC = 64;
   layer_FX = 3;
   layer_FY = 3;
   layer_BLOCK_SIZE = 64;

   // Fake conv2d
//    glb_base_addr = 1310720;

   // submodule_2 (residual relu), conv2d_mx_default_11
   glb_base_addr = 0;

    // FIXME: These paths are hardcoded for now. In the future, they should be set in a more streamlined way
   inputActivation_filename = "/aha/submodule_2/tensor_files/input_hex.txt";
   inputActivation_size = layer_X * layer_Y * layer_IC;
   inputActivation_size_aligned = $ceil(real'(inputActivation_size)/32.0) * 32.0;
   inputActivation_start_addr = glb_base_addr;
   inputActivation = parse_8b_data(inputActivation_filename, inputActivation_size);

   inputScale_size = layer_IC/layer_BLOCK_SIZE * layer_X * layer_Y;
   inputScale_size_aligned = $ceil(real'(inputScale_size)/32.0) * 32.0;
   inputScale_start_addr = inputActivation_start_addr + int'(inputActivation_size_aligned);
   inputScale_filename = "/aha/submodule_2/tensor_files/inputScale_hex.txt";
   inputScale = parse_8b_data(inputScale_filename, inputScale_size);

   weight_size = layer_OC * layer_IC * layer_FX * layer_FY;
   weight_size_aligned = $ceil(real'(weight_size)/32.0) * 32.0;
   weight_start_addr = inputScale_start_addr + int'(inputScale_size_aligned);
   weight_filename = "/aha/submodule_2/tensor_files/weight_hex.txt";
   weight = parse_8b_data(weight_filename, weight_size);

   weightScale_size = layer_OC * layer_IC/layer_BLOCK_SIZE * layer_FX * layer_FY;
   weightScale_size_aligned = $ceil(real'(weightScale_size)/32.0) * 32.0;
   weightScale_start_addr = weight_start_addr + int'(weight_size_aligned);
   weightScale_filename = "/aha/submodule_2/tensor_files/weightScale_hex.txt";
   weightScale = parse_8b_data(weightScale_filename, weightScale_size);

   bias_size = layer_OC;
   bias_start_addr = weightScale_start_addr + int'(weightScale_size_aligned);
   bias_filename = "/aha/submodule_2/tensor_files/bias_hex.txt";
   bias = parse_16b_data(bias_filename, bias_size);

    // Hardcoding this for now. In the future, it should be set appropriately
    matrix_params_size = 20;
    matrix_params_filename = "/aha/submodule_2/serialized_matrix_params.txt";
    serialized_matrix_params = parse_32b_data(matrix_params_filename, matrix_params_size);

    $display("\nDnnLayer object successfully created\n");

endfunction


// assertion
function void DnnLayer::assertion(bit cond, string msg);
    assert (cond)
    else begin
        $display("%s", msg);
        $stacktrace;
        $finish(1);
    end
endfunction


function byte_array_t DnnLayer::parse_8b_data(string filename, int size);
    int cnt = 0;
    byte_array_t result = new[size];

    int fp = $fopen(filename, "r");
    $display("[%0t] Reading dnn layer params from %s", $time, filename);
    assertion(fp != 0, "Unable to read file!");
    while (!$feof(
        fp
    )) begin
        int unsigned data;
        int code;

`ifdef verilator
        code = $fscanf(fp, "%x", data);
`else
        code = $fscanf(fp, "%04x", data);
`endif
        // Quick check to see if it's working at all, can compare to contents of file
        if (cnt<4) $display(" - got data %04x", data);
        if (code == -1) continue;
        assertion(code == 1, $sformatf(
                "Incorrect data format. Expected 1 entry, got: %0d. Current entires: %0d",
                code,
                result.size()
                ));
        result[cnt++] = data;
    end

    assertion(cnt == (size), $sformatf(
            "Unable to data. Parsed size is %0d, while expected size is %0d\n",
            cnt,
            size
            ));

    $display(("[%0t] Successfully read %0d dnn layer params from file %s"), $time, cnt, filename);
    $fclose(fp);
    return result;
endfunction


function half_array_t DnnLayer::parse_16b_data(string filename, int size);
    int cnt = 0;
    half_array_t result = new[size];

    int fp = $fopen(filename, "r");
    $display("[%0t] Reading dnn layer params from %s", $time, filename);
    assertion(fp != 0, "Unable to read file!");
    while (!$feof(
        fp
    )) begin
        int unsigned data;
        int code;

`ifdef verilator
        code = $fscanf(fp, "%x", data);
`else
        code = $fscanf(fp, "%04x", data);
`endif
        // Quick check to see if it's working at all, can compare to contents of file
        if (cnt<4) $display(" - got data %04x", data);
        if (code == -1) continue;
        assertion(code == 1, $sformatf(
                "Incorrect data format. Expected 1 entry, got: %0d. Current entires: %0d",
                code,
                result.size()
                ));
        result[cnt++] = data;
    end

    assertion(cnt == (size), $sformatf(
            "Unable to data. Parsed size is %0d, while expected size is %0d\n",
            cnt,
            size
            ));

    $display(("[%0t] Successfully read %0d dnn layer params from file %s"), $time, cnt, filename);
    $fclose(fp);
    return result;
endfunction


function matrix_params_array_t DnnLayer::parse_32b_data(string filename, int size);
    int cnt = 0;
    matrix_params_array_t result = new[size];

    int fp = $fopen(filename, "r");
    $display("[%0t] Reading serialized matrix params from %s", $time, filename);
    assertion(fp != 0, "Unable to read file!");
    while (!$feof(
        fp
    )) begin
        int unsigned data;
        int code;

`ifdef verilator
        code = $fscanf(fp, "%x", data);
`else
        code = $fscanf(fp, "%08x", data);
`endif
        // Quick check to see if it's working at all, can compare to contents of file
        if (cnt<4) $display(" - got data %08x", data);
        if (code == -1) continue;
        assertion(code == 1, $sformatf(
                "Incorrect data format. Expected 1 entry, got: %0d. Current entires: %0d",
                code,
                result.size()
                ));
        result[cnt++] = data;
    end

    assertion(cnt == (size), $sformatf(
            "Unable to data. Parsed size is %0d, while expected size is %0d\n",
            cnt,
            size
            ));

    $display(("[%0t] Successfully read %0d serialized matrix params from file %s"), $time, cnt, filename);
    $fclose(fp);
    return result;
endfunction