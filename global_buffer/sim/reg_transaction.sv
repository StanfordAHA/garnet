/*=============================================================================
** Module: reg_transaction.sv
** Description:
**              program for configuration transaction
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/
class RegTransaction #(int ADDR_WIDTH = 12) extends Transaction;
    bit                        wr_en;
    bit                        wr_clk_en;
    bit [ADDR_WIDTH-1:0]       wr_addr;
    bit [AXI_DATA_WIDTH-1:0]   wr_data;
    bit                        rd_en;
    bit                        rd_clk_en;
    bit [ADDR_WIDTH-1:0]       rd_addr;
    bit [AXI_DATA_WIDTH-1:0]   rd_data;
    bit                        rd_data_valid;

    extern function new();
    extern function RegTransaction copy(RegTransaction to=null);
    extern function void display();

endclass

function RegTransaction::new();
endfunction

function RegTransaction RegTransaction::copy(RegTransaction to=null);
    if (to == null) copy = new();
    else            copy = to;
    copy.trans_type = this.trans_type;
    copy.wr_en      = this.wr_en;
    copy.wr_clk_en  = this.wr_clk_en;
    copy.wr_addr    = this.wr_addr;
    copy.wr_data    = this.wr_data;
    copy.rd_en      = this.rd_en;
    copy.rd_clk_en  = this.rd_clk_en;
    copy.rd_addr    = this.rd_addr;
    copy.rd_data    = this.rd_data;
    copy.rd_data_valid = this.rd_data_valid;
    return copy;
endfunction


function void RegTransaction::display();
    $display("Transaction type: %s, \t Transaction number: %0d \n \
             wr_en: %0d, wr_addr: 0x%0h, wr_data: 0x%0h, rd_en: %0d, rd_addr: 0x%0h \n",
             trans_type.name(), no_trans, wr_en, wr_addr, wr_data, rd_en, rd_addr);
endfunction
