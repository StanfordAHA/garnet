/*=============================================================================
** Module: reg_transaction.sv
** Description:
**              program for configuration transaction
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

import global_buffer_param::*;

class RegTransaction extends Transaction;
    rand bit                        wr_en;
    rand bit                        wr_clk_en;
    rand bit [AXI_ADDR_WIDTH-1:0]   wr_addr;
    rand bit [AXI_DATA_WIDTH-1:0]   wr_data;
    rand bit                        rd_en;
    rand bit                        rd_clk_en;
    rand bit [AXI_ADDR_WIDTH-1:0]   rd_addr;
         bit [AXI_DATA_WIDTH-1:0]   rd_data;
         bit                        rd_data_valid;

    constraint clk_en_c {
        // clk enable is same as enable
        wr_en == wr_clk_en;
        rd_en == rd_clk_en;
    };

    constraint wr_rd_c {
        // generate any one among write and read
        wr_en != rd_en;
    };
    constraint addr_c {
        solve wr_en before wr_addr;
        solve rd_en before rd_addr;
        // address is aligned to bank_data_width
        if (wr_en) {
            wr_addr[AXI_BYTE_OFFSET-1:0] == {AXI_BYTE_OFFSET{1'b0}};
            rd_addr == 0;
        } else {
            wr_addr == 0;
            rd_addr[AXI_BYTE_OFFSET-1:0] == {AXI_BYTE_OFFSET{1'b0}};
        }
    };

    extern function new();
    extern function RegTransaction copy(RegTransaction to=null);
    extern function void display();

endclass

function RegTransaction::new();
    this.trans_type = REG;
endfunction

function RegTransaction RegTransaction::copy(RegTransaction to=null);
    if (to == null) copy = new();
    else            copy = to;
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
