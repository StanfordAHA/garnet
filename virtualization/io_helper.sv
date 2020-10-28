/*=============================================================================
** Module: io_helper.sv
** Description:
**              io helper class
** Author: Keyi Zhang, Taeyoung Kong
** Change history:  10/24/2020 - Implement the first version
**===========================================================================*/
class IOHelper;
    // read input data
    static function data_array_t get_input_data(string filename);
        byte unsigned result[$];
        int fp = $fopen(filename, "rb");
        assert_(fp != 0, "Unable to read input file");
        while (!$feof(fp)) begin
            byte unsigned value;
            int code;
            code = $fread(value, fp);
            if (code != 1) break;
            result.push_back(value);
        end
        $fclose(fp);
        return result;
    endfunction

    // read bitstream
    static function bitstream_t get_bitstream(string bitstream_filename);
        bitstream_t result;
        int fp = $fopen(bitstream_filename, "r");
        assert_(fp != 0, "Unable to read bitstream file");
        while (!$feof(fp)) begin
            int unsigned addr;
            int unsigned data;
            int code;
            bitstream_entry_t entry;
            code = $fscanf(fp, "%08x %08x", entry.addr, entry.data);
            if (code == -1) continue;
            assert_(code == 2 , $sformatf("Incorrect bs format. Expected 2 entries, got: %d. Current entires: %d", code, result.size()));
            result.push_back(entry);
        end
        return result;
    endfunction

    // read gold result data
    static function data_array_t get_gold_data(string filename);
        byte unsigned result[$];
        byte unsigned value;
        int fp, code;
        fp = $fopen(filename, "rb");
        assert_(fp != 0, "Unable to read gold file");
        while (!$feof(fp)) begin
            code = $fread(value, fp);
            if (code)
                result.push_back(value);
        end
        return result;
    endfunction

    // assertion
    static function void assert_(bit cond, string msg);
        assert (cond) else begin
            $display("%s", msg);
            $stacktrace;
            $finish(1);
        end
    endfunction

endclass

