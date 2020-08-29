/*=============================================================================
** Module: proc_transaction.sv
** Description:
**              program for processor transaction
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/
class ProcTransaction extends Transaction;
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
    }

    constraint addr_c {
        solve wr_en before wr_addr;
        solve rd_en before rd_addr;
        // address is aligned to bank_data_width
        if (wr_en) {
            wr_addr[BANK_BYTE_OFFSET-1:0] == {BANK_BYTE_OFFSET{1'b0}};
            rd_addr == 0;
        } else {
            wr_addr == 0;
            rd_addr[BANK_BYTE_OFFSET-1:0] == {BANK_BYTE_OFFSET{1'b0}};
        }
    }

    constraint max_length_c {
        // length is bigger than 0
        length > 0;
        // length is equal to or less than 256
        length <= 256;
    }

    constraint arr_size_c {
        solve length before wr_data;
        solve length before wr_strb;
        if (wr_en) {
            wr_data.size() == length;
            wr_strb.size() == length;
        } else {
            wr_data.size() == 0;
            wr_strb.size() == 0;
        }
    }

    extern function new();
    extern function void display();
    extern function void post_randomize();
    extern function ProcTransaction copy(ProcTransaction to=null);

endclass

function ProcTransaction::new();
    this.trans_type = PROC;
endfunction

function void ProcTransaction::post_randomize();
    if (rd_en) begin
        rd_data = new[length];
        rd_data_valid = new[length];
    end
endfunction

function ProcTransaction ProcTransaction::copy(ProcTransaction to=null);
    if (to == null) copy = new();
    else            copy = to;
    copy.length  = this.length;
    copy.wr_en   = this.wr_en;
    copy.wr_strb = this.wr_strb;
    copy.wr_addr = this.wr_addr;
    copy.wr_data = this.wr_data;
    copy.rd_en   = this.rd_en;
    copy.rd_addr = this.rd_addr;
    copy.rd_data = this.rd_data;
    copy.rd_data_valid = this.rd_data_valid;
    return copy;
endfunction

function void ProcTransaction::display();
    $display("Transaction type: %s, \t Transaction number: %0d \n \
             length: %0d, wr_en: %0d, wr_addr: 0x%0h, rd_en: %0d, rd_addr: 0x%0h \n",
             trans_type.name(), no_trans, length, wr_en, wr_addr, rd_en, rd_addr);
endfunction
