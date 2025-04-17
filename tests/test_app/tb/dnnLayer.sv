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

typedef bit[31:0] float_bits_t;

class DnnLayer;

    byte_array_t inputActivation;
    byte_array_t weight;
    half_array_t bias;
    byte_array_t inputScale;
    byte_array_t weightScale;

    // Have some metadata to store the shape of each tensor and its resultant total size
    int inputActivation_size;
    int weight_size;
    int bias_size;
    int inputScale_size;
    int weightScale_size;

    string inputActivation_filename;
    string weight_filename;
    string bias_filename;
    string inputScale_filename;
    string weightScale_filename;

    extern function new();
    extern function byte_array_t parse_8b_data(string filename, int size);
    extern function half_array_t parse_16b_data(string filename, int size);
    extern function void assertion(bit cond, string msg);


endclass



function DnnLayer::new();

    // FIXME: Provide the correct path to the input data
    inputActivation_filename = "/aha/network_params/input_hex.txt";
    // Hardcoding for conv2_x for now. In the future, this should be set by reading the model.txt file
    inputActivation_size = 200704;
    inputActivation = parse_8b_data(inputActivation_filename, inputActivation_size);

    weight_size = 36864;
    weight_filename = "/aha/network_params/weight_hex.txt";
    weight = parse_8b_data(weight_filename, weight_size);

    bias_size = 64;
    bias_filename = "/aha/network_params/bias_hex.txt";
    bias = parse_16b_data(bias_filename, bias_size);

    $display("First 10 elements of bias: ");
    for (int i = 0; i < 10; i++) begin
        $display("%0d: %0h", i, bias[i]);
    end

    inputScale_size = 3136;
    inputScale_filename = "/aha/network_params/inputScale_hex.txt";
    inputScale = parse_8b_data(inputScale_filename, inputScale_size);

    weightScale_size = 576;
    weightScale_filename = "/aha/network_params/weightScale_hex.txt";
    weightScale = parse_8b_data(weightScale_filename, weightScale_size);

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

function bit [31:0] swap32(input bit [31:0] val);
  return { val[7:0], val[15:8], val[23:16], val[31:24] };
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