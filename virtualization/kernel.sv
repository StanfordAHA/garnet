/*=============================================================================
** Module: kernel.sv
** Description:
**              kernel class
** Author: Taeyoung Kong
** Change history:
**  10/25/2020 - Implement the first version
**===========================================================================*/

import "DPI-C" function chandle parse_placement(string filename);
import "DPI-C" function chandle parse_metadata(string filename);

import "DPI-C" function int get_num_groups(chandle info);
import "DPI-C" function int get_num_inputs(chandle info);
import "DPI-C" function int get_num_outputs(chandle info);
import "DPI-C" function int get_input_x(chandle info, int index);
import "DPI-C" function int get_input_y(chandle info, int index);
import "DPI-C" function int get_output_x(chandle info, int index);
import "DPI-C" function int get_output_y(chandle info, int index);
import "DPI-C" function int get_reset_index(chandle info);

import "DPI-C" function string get_placement_filename(chandle info);
import "DPI-C" function string get_bitstream_filename(chandle info);
import "DPI-C" function string get_input_filename(chandle info, int index);
import "DPI-C" function string get_output_filename(chandle info, int index);
import "DPI-C" function int get_input_size(chandle info);
import "DPI-C" function int get_output_size(chandle info);

typedef enum int {
    IDLE = 0,
    QUEUED = 1,
    CONFIG = 2,
    RUNNING = 3,
    FINISH = 4
} app_state_t;

typedef struct packed {
    int unsigned addr;
    int unsigned data;
} bitstream_entry_t;

typedef byte unsigned data_array_t[$];
typedef bitstream_entry_t bitstream_t[$];

class Kernel;
    int id;

    // queue to store data
    data_array_t input_data;
    data_array_t output_data;
    data_array_t gold_data;
    // queue to store bitstream
    bitstream_t  bitstream;
    // app state
    app_state_t  app_state;

    // column start and end
    int column_start;
    int column_end;

    // data start and end
    int input_bank_start;
    int input_bank_end;
    int output_bank_start;
    int output_bank_end;

    extern function new(int id, bitstream_t bitstream, data_array_t input_data, data_array_t gold_data);
    extern function void display();
    extern function void print_input();
    extern function void print_output();
    extern function void print_gold();
    extern function void print_bitstream();
    extern function void compare();
endclass

function Kernel::new(int id, bitstream_t bitstream, data_array_t input_data, data_array_t gold_data);
    this.id = id;
    this.bitstream = bitstream;
    this.input_data = input_data;
    this.gold_data = gold_data;
endfunction

function void Kernel::display();
    $display("Kernel number: %0d, \n \
              column start: %0d, column end: %0d, \n \
              input bank start: %0d, input bank end: %0d, \n \
              output bank start: %0d, output bank end: %0d",
              id, column_start, column_end,
              input_bank_start, input_bank_end, output_bank_start, output_bank_end);
endfunction

function void Kernel::compare();
    assert (gold_data.size() != output_data.size())
    else begin
        $display("APP[%0d], gold data size is %0d, output data size is %0d", id, gold_data.size(), output_data.size());
        $finish(2);
    end
    for (int i = 0; i < gold_data.size(); i++) begin
        IOHelper::assert_(gold_data[i] == output_data[i],
        $sformatf("APP[%0d], pixel[%0d] Get %02X but expect %02X", id, i, output_data[i], gold_data[i]));
    end
    $display("APP %0d passed", id);
endfunction

function void Kernel::print_input();
    foreach(input_data[i]) begin
        $write("%02X ", input_data[i]);
    end
    $display("\n");
endfunction

function void Kernel::print_gold();
    foreach(gold_data[i]) begin
        $write("%02X ", gold_data[i]);
    end
    $display("\n");
endfunction

function void Kernel::print_output();
    foreach(output_data[i]) begin
        $write("%02X ", output_data[i]);
    end
    $display("\n");
endfunction

function void Kernel::print_bitstream();
    foreach(bitstream[i]) begin
        $display("%16X", bitstream[i]);
    end
    $display("\n");
endfunction
