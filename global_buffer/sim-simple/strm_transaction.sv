/*=============================================================================
** Module: strm_transaction.sv
** Description:
**              program for configuration transaction
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/
class StrmTransaction extends Transaction;

    rand bit [TILE_SEL_ADDR_WIDTH-1:0] tile;
    rand bit                        st_on;
    rand bit [GLB_ADDR_WIDTH-1:0]   st_addr;
    rand bit [CGRA_DATA_WIDTH-1:0]  st_data [];
    rand int                        st_length;

    rand bit                        ld_on;
    rand bit [GLB_ADDR_WIDTH-1:0]   ld_addr;
         bit [CGRA_DATA_WIDTH-1:0]  ld_data [];
    rand int                        ld_length;

    constraint length_c {
        // length is bigger than 0
        st_length > 0;
        ld_length > 0;
        // length is equal to or less than 256
        st_length <= 256;
        ld_length <= 256;
    }

    constraint addr_c {
        solve st_on before st_addr;
        solve ld_on before ld_addr;
        // address is aligned to cgra_data_width
        if (st_on) {
            st_addr[CGRA_BYTE_OFFSET-1:0] == {CGRA_BYTE_OFFSET{1'b0}};
        } else {
            st_addr == 0;
        }
        if (ld_on) {
            ld_addr[CGRA_BYTE_OFFSET-1:0] == {CGRA_BYTE_OFFSET{1'b0}};
        } else {
            ld_addr == 0;
        }
    }

    constraint data_c {
        solve st_length before st_data;
        if (st_on) {
            st_data.size() == st_length;
        } else {
            st_data.size() == 0;
        }
    }

    extern function new();
    extern function void post_randomize();
    extern function StrmTransaction copy(StrmTransaction to=null);
    extern function void display();

endclass

function StrmTransaction::new();
    this.trans_type = STRM;
endfunction

function void StrmTransaction::post_randomize();
    if (ld_on) begin
        ld_data = new[ld_length];
    end
endfunction

function StrmTransaction StrmTransaction::copy(StrmTransaction to=null);
    if (to == null) copy = new();
    else            copy = to;
    copy.tile       = this.tile;
    copy.ld_on      = this.ld_on;
    copy.ld_addr    = this.ld_addr;
    copy.ld_data    = this.ld_data;
    copy.ld_length  = this.ld_length;
    copy.st_on      = this.st_on;
    copy.st_addr    = this.st_addr;
    copy.st_data    = this.st_data;
    copy.st_length  = this.st_length;
    return copy;
endfunction

function void StrmTransaction::display();
    $display("Transaction type: %s, \t Transaction number: %0d \n \
             ld_on: %0d, ld_addr: 0x%0h, ld_length: %0d, st_on: %0d, st_addr: 0x%0h, st_length: %0d \n",
             trans_type.name(), no_trans, ld_on, ld_addr, ld_length, st_on, st_addr, st_length);
endfunction
