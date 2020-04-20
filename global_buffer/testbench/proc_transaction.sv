/*=============================================================================
** Module: proc_transaction.sv
** Description:
**              program for processor transaction
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

import global_buffer_param::*;

class procTransaction;
    rand bit                         wr_en;
    rand bit [BANK_DATA_WIDTH/8-1:0] wr_strb [];
    rand bit [GLB_ADDR_WIDTH-1:0]    wr_addr;
    rand bit [BANK_DATA_WIDTH-1:0]   wr_data [];
    rand bit                         rd_en;
    rand bit [GLB_ADDR_WIDTH-1:0]    rd_addr;
         bit [BANK_DATA_WIDTH-1:0]   rd_data [];
         bit                         rd_data_valid [];
    rand int                         length;

    constraint wr_rd_c {
        // generate any one among write and read
        wr_en != rd_en;
    };
    constraint addr_c {
        solve wr_en before wr_addr;
        solve rd_en before rd_addr;
        // address is aligned to bank_data_width
        if (wr_en) {
            wr_addr[BANK_BYTE_OFFSET-1:0] == {BANK_BYTE_OFFSET{1'b0}};
        } else {
            rd_addr[BANK_BYTE_OFFSET-1:0] == {BANK_BYTE_OFFSET{1'b0}};
        }
    };
    constraint max_length_c {
        // length is bigger than 0
        length > 0;
        // length is equal to or less than 256
        length <= 256;
    };
    constraint arr_size_c {
        solve length before wr_data;
        solve length before wr_strb;
        if (wr_en) {
            wr_data.size() == length;
            wr_strb.size() == length;
        }
    }

    extern function allocate();

endclass

function procTransaction::allocate();
    rd_data = new[length];
    rd_data_valid = new[length];
endfunction
