/*=============================================================================
** Module: proc_transaction.sv
** Description:
**              processor transaction
** Author: Taeyoung Kong
** Change history:
**  10/12/2020 - Implement the first version
**===========================================================================*/
class ProcTransaction;
    bit                         write;
    bit                         read;
    bit [TILE_SEL_ADDR_WIDTH+BANK_SEL_ADDR_WIDTH-1:0] start_bank; //2^5
    bit [BANK_ADDR_WIDTH-1:0]   start_addr; //2^17
    bit [BANK_DATA_WIDTH-1:0]   wr_data [];
    bit [BANK_DATA_WIDTH-1:0]   rd_data [];
    int                         length;
    extern function new();
    extern function void display();
    extern function ProcTransaction copy(ProcTransaction to=null);
endclass

function ProcTransaction::new();
    this.trans_type = PROC;
endfunction

function ProcTransaction ProcTransaction::copy(ProcTransaction to=null);
    if (to == null) copy = new();
    else            copy = to;
    copy.length     = this.length;
    copy.write      = this.write;
    copy.read       = this.read;
    copy.start_addr = this.start_addr;
    copy.wr_data    = this.wr_data;
    copy.rd_data    = this.rd_data;
    return copy;
endfunction

function void ProcTransaction::display();
    if (write) begin
        $display("Transaction type: %s WRITE, \t Transaction number: %0d \n \
                 size: %0d Bytes, start_addr: 0x%0h \n",
                 trans_type.name(), no_trans, length*BANK_DATA_WIDTH/8, start_addr);
    end
    else begin
        $display("Transaction type: %s READ, \t Transaction number: %0d \n \
                 size: %0d Bytes, start_addr: 0x%0h \n",
                 trans_type.name(), no_trans, length*BANK_DATA_WIDTH/8, start_addr);
    end
endfunction
