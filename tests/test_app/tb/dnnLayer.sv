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

typedef struct {
        byte_array_t tensor_8b;
        int size;
        int start_addr;
        int tensor_exists; // Indicates if the tensor exists
} tensor_8b_info_t;

typedef struct {
        half_array_t tensor_16b;
        int size;
        int start_addr;
        int tensor_exists; // Indicates if the tensor exists
} tensor_16b_info_t;

typedef struct {
        matrix_params_array_t tensor_32b;
        int size;
} tensor_32b_info_t;

class DnnLayer;
    tensor_8b_info_t inputActivation_info;
    tensor_8b_info_t inputScale_info;
    tensor_8b_info_t weight_info;
    tensor_8b_info_t weightScale_info;
    tensor_16b_info_t bias_info;
    tensor_32b_info_t serialized_matrix_params_info;

    string inputActivation_filename;
    string weight_filename;
    string bias_filename;
    string inputScale_filename;
    string weightScale_filename;
    string matrix_params_filename;

    extern function new();
    extern function read_params(string app_dir);
    extern function tensor_8b_info_t parse_8b_data(string filename);
    extern function tensor_16b_info_t parse_16b_data(string filename);
    extern function tensor_32b_info_t parse_32b_data(string filename);
    extern function void assertion(bit cond, string msg);


endclass



function DnnLayer::new();
    // Constructor for the DnnLayer class. Doesn't actually do anything other than initialize the object
endfunction



function DnnLayer::read_params(string app_dir);

   inputActivation_filename = {app_dir, "/tensor_files/input_hex.txt"};
   inputActivation_info = parse_8b_data(inputActivation_filename);

   inputScale_filename = {app_dir, "/tensor_files/inputScale_hex.txt"};
   inputScale_info = parse_8b_data(inputScale_filename);

   weight_filename = {app_dir, "/tensor_files/weight_hex.txt"};
   weight_info = parse_8b_data(weight_filename);

   weightScale_filename = {app_dir, "/tensor_files/weightScale_hex.txt"};
   weightScale_info = parse_8b_data(weightScale_filename);

   bias_filename = {app_dir, "/tensor_files/bias_hex.txt"};
   bias_info = parse_16b_data(bias_filename);

   matrix_params_filename = {app_dir, "/serialized_matrix_params.txt"};;
   serialized_matrix_params_info = parse_32b_data(matrix_params_filename);

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


function tensor_8b_info_t DnnLayer::parse_8b_data(string filename);
    int cnt = 0;
    int size;
    int tensor_exists;
    int start_addr;
    tensor_8b_info_t result;
    string line;

    int fp = $fopen(filename, "r");
    $display("[%0t] Reading dnn layer params from %s", $time, filename);
    assertion(fp != 0, "Unable to read file!");


    // Read and parse tensor exists (true or false) from the first line
    void'($fgets(line, fp));
    if (!$sscanf(line, "TENSOR_EXISTS: %d", tensor_exists)) begin
        $fatal(1, "Expected first line in file to be 'TENSOR_EXISTS: <0|1>', got: %s", line);
    end
    if (tensor_exists == 0) begin
        $display("INFO: %s indicates that tensor does not exist. Returning empty tensor.", filename);
        result.tensor_exists = 0;
        result.size = 0;
        result.start_addr = 0;
        $fclose(fp);
        return result;
    end else if (tensor_exists == 1) begin
        result.tensor_exists = 1;
    end else begin
        $fatal(1, "Expected first line in file to be 'TENSOR_EXISTS: <0|1>', got: %s", line);
    end

    // Read and parse the size from the second line
    void'($fgets(line, fp));
    if (!$sscanf(line, "SIZE: %d", size)) begin
        $fatal(1, "Expected second line in file to be 'SIZE: <int>', got: %s", line);
    end

    // Read and parse the start addr from the third line
    void'($fgets(line, fp));
    if (!$sscanf(line, "START_ADDR: %d", start_addr)) begin
        $fatal(1, "Expected third line in file to be 'START_ADDR: <int>', got: %s", line);
    end


    result.size = size;
    result.start_addr = start_addr;
    result.tensor_8b = new[size];

    while (!$feof(fp)) begin
        int unsigned data;
        int code;

    `ifdef verilator
        code = $fscanf(fp, "%x", data);
    `else
        code = $fscanf(fp, "%04x", data);
    `endif

        // Quick check to see if it's working at all, can compare to contents of file
        if (cnt < 4) $display(" - got data %04x", data);
        if (code == -1) continue;
        assertion(code == 1, $sformatf(
            "Incorrect data format. Expected 1 entry, got: %0d. Current entries: %0d",
            code,
            result.tensor_8b.size()
        ));
        result.tensor_8b[cnt++] = data;
    end

    assertion(cnt == size, $sformatf(
        "Unable to load data. Parsed size is %0d, while expected size is %0d\n",
        cnt,
        size
    ));

    $display("[%0t] Successfully read %0d dnn layer params from file %s", $time, cnt, filename);
    $fclose(fp);
    return result;
endfunction



function tensor_16b_info_t DnnLayer::parse_16b_data(string filename);
    int cnt = 0;
    int size;
    int tensor_exists;
    int start_addr;
    tensor_16b_info_t result;
    string line;

    int fp = $fopen(filename, "r");
    $display("[%0t] Reading dnn layer params from %s", $time, filename);
    assertion(fp != 0, "Unable to read file!");


    // Read and parse tensor exists (true or false) from the first line
    void'($fgets(line, fp));
    if (!$sscanf(line, "TENSOR_EXISTS: %d", tensor_exists)) begin
        $fatal(1, "Expected first line in file to be 'TENSOR_EXISTS: <0|1>', got: %s", line);
    end
    if (tensor_exists == 0) begin
        $display("INFO: %s indicates that tensor does not exist. Returning empty tensor.", filename);
        result.tensor_exists = 0;
        result.size = 0;
        result.start_addr = 0;
        $fclose(fp);
        return result;
    end else if (tensor_exists == 1) begin
        result.tensor_exists = 1;
    end else begin
        $fatal(1, "Expected first line in file to be 'TENSOR_EXISTS: <0|1>', got: %s", line);
    end

    // Read and parse the size from the second line
    void'($fgets(line, fp));
    if (!$sscanf(line, "SIZE: %d", size)) begin
        $fatal(1, "Expected second line in file to be 'SIZE: <int>', got: %s", line);
    end

    // Read and parse the start addr from the third line
    void'($fgets(line, fp));
    if (!$sscanf(line, "START_ADDR: %d", start_addr)) begin
        $fatal(1, "Expected third line in file to be 'START_ADDR: <int>', got: %s", line);
    end

    result.size = size;
    result.start_addr = start_addr;
    result.tensor_16b = new[size];

    while (!$feof(fp)) begin
        int unsigned data;
        int code;

    `ifdef verilator
        code = $fscanf(fp, "%x", data);
    `else
        code = $fscanf(fp, "%04x", data);
    `endif

        // Quick check to see if it's working at all, can compare to contents of file
        if (cnt < 4) $display(" - got data %04x", data);
        if (code == -1) continue;
        assertion(code == 1, $sformatf(
            "Incorrect data format. Expected 1 entry, got: %0d. Current entries: %0d",
            code,
            result.tensor_16b.size()
        ));
        result.tensor_16b[cnt++] = data;
    end

    assertion(cnt == size, $sformatf(
        "Unable to load data. Parsed size is %0d, while expected size is %0d\n",
        cnt,
        size
    ));

    $display("[%0t] Successfully read %0d dnn layer params from file %s", $time, cnt, filename);
    $fclose(fp);
    return result;
endfunction


function tensor_32b_info_t DnnLayer::parse_32b_data(string filename);
    int cnt = 0;
    int size;
    tensor_32b_info_t result;
    string line;

    int fp = $fopen(filename, "r");
    $display("[%0t] Reading serialized matrix params from %s", $time, filename);
    assertion(fp != 0, "Unable to read file!");

    // Read and parse the size from the first line
    void'($fgets(line, fp));
    if (!$sscanf(line, "SIZE: %d", size)) begin
        $fatal(1, "Expected first line in file to be 'SIZE: <int>', got: %s", line);
    end

    result.size = size;
    result.tensor_32b = new[size];

    while (!$feof(fp)) begin
        int unsigned data;
        int code;

    `ifdef verilator
        code = $fscanf(fp, "%x", data);
    `else
        code = $fscanf(fp, "%08x", data);
    `endif

        // Quick check to see if it's working at all, can compare to contents of file
        if (cnt < 4) $display(" - got data %08x", data);
        if (code == -1) continue;
        assertion(code == 1, $sformatf(
            "Incorrect data format. Expected 1 entry, got: %0d. Current entries: %0d",
            code,
            result.tensor_32b.size()
        ));
        result.tensor_32b[cnt++] = data;
    end

    assertion(cnt == size, $sformatf(
        "Unable to load data. Parsed size is %0d, while expected size is %0d\n",
        cnt,
        size
    ));

    $display("[%0t] Successfully read %0d serialized matrix params from file %s", $time, cnt, filename);
    $fclose(fp);
    return result;
endfunction
