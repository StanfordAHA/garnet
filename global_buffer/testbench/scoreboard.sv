/*=============================================================================
** Module: Scoreboard.sv
** Description:
**              Scoreboard class
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

class Scoreboard;

    // create mailbox handle
    mailbox p_mon2scb;

    // used to count the number of transactions
    int no_trans;

    // global_buffer array
    bit [BANK_DATA_WIDTH:0] mem [2**GLB_ADDR_WIDTH];

    extern function new(mailbox p_mon2scb);
    extern task run();

endclass

function Scoreboard::new(mailbox p_mon2scb);
    // getting the mailbox handles from environment
    this.p_mon2scb = p_mon2scb;

    // initialize to zero
    foreach(mem[i]) mem[i] = 0;
endfunction

task Scoreboard::run();
    forever begin
        // declare transaction
        ProcTransaction trans;

        p_mon2scb.get(trans);

        if(trans.wr_en) begin
            foreach(trans.wr_data[i]) begin
                for (int j=0; j<BANK_DATA_WIDTH/8; j++) begin
                    mem[trans.wr_addr+8*i][j*8+:8] = ({8{trans.wr_strb[i][j]}} | trans.wr_data[i][j*8+:8]);
                end
            end
        end
        else begin
            foreach(trans.rd_data[i]) begin
                if((mem[trans.rd_addr+8*i] != trans.rd_data[i]) || ~trans.rd_data_valid[i]) begin
                    $error("[SCB-FAIL] Addr = %0h, \n \t Data :: Expected = %0h Actual = %0h",
                           trans.rd_addr+8*i, mem[trans.rd_addr+8*i], trans.rd_data[i]); 
                end
                else begin
                    // $display("[SCB-PASS] Addr = %0h, \n \t Data :: Expected = %0h Actual = %0h",
                    //          trans.rd_addr+8*i, mem[trans.rd_addr+8*i], trans.rd_data[i]); 
                end
            end
        end
        no_trans++;
    end
endtask
