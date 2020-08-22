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
    mailbox r_mon2scb;
    mailbox s_mon2scb [NUM_GLB_TILES];

    // used to count the number of transactions
    int no_trans;

    // global_buffer array
    bit [BANK_DATA_WIDTH-1:0] mem [2**GLB_ADDR_WIDTH];

    // global_buffer config register file
    bit [AXI_DATA_WIDTH-1:0] reg_rf [2**AXI_ADDR_WIDTH];

    extern function new(mailbox p_mon2scb, mailbox r_mon2scb, mailbox s_mon2scb[]);
    extern task run();
    extern task proc_run();
    extern task reg_run();

endclass

function Scoreboard::new(mailbox p_mon2scb, mailbox r_mon2scb, mailbox s_mon2scb[]);
    // no_trans
    no_trans = 0;

    // getting the mailbox handles from environment
    this.p_mon2scb = p_mon2scb;
    this.r_mon2scb = r_mon2scb;
    this.s_mon2scb = s_mon2scb;

    // initialize to zero
    foreach(mem[i])     mem[i] = 0;
    foreach(reg_rf[i])  reg_rf[i] = 0;
endfunction

task Scoreboard::run();
    fork
        proc_run();
        reg_run();
    join_none
endtask

task Scoreboard::proc_run();
    forever begin
        ProcTransaction p_trans;
        p_mon2scb.get(p_trans);
        if(p_trans.wr_en) begin
            foreach(p_trans.wr_data[i]) begin
                for (int j=0; j<BANK_DATA_WIDTH/8; j++) begin
                    if(p_trans.wr_strb[i][j]) begin
                        mem[p_trans.wr_addr+8*i][j*8+:8] = p_trans.wr_data[i][j*8+:8];
                    end
                end
            end
        end
        else if (p_trans.rd_en) begin
            foreach(p_trans.rd_data[i]) begin
                if(mem[p_trans.rd_addr+8*i] != p_trans.rd_data[i]) begin
                    // $error("[SCB-FAIL] #Trans = %0d, Addr = 0x%0h, \n \t Data :: Expected = 0x%0h Actual = 0x%0h",
                    //       p_trans.no_trans, p_trans.rd_addr+8*i, mem[p_trans.rd_addr+8*i], p_trans.rd_data[i]); 
                end
                else if (~p_trans.rd_data_valid[i]) begin
                    // $error("[SCB-FAIL] #Trans = %0d, rd_data_valid signal is not asserted", p_trans.no_trans);
                end
                else begin
                    // $display("[SCB-PASS] Addr = 0x%0h, \n \t Data :: Expected = 0x%0h Actual = 0x%0h",
                    //          p_trans.rd_addr+8*i, mem[p_trans.rd_addr+8*i], p_trans.rd_data[i]); 
                end
            end
        end
        no_trans++;
    end
endtask

task Scoreboard::reg_run();
    forever begin
        RegTransaction  r_trans;
        r_mon2scb.get(r_trans);
        if(r_trans.wr_en) begin
            $display("[REG-WRITE] #Reg Trans = %0d, Addr = 0x%0h, Data 0x%0h", r_trans.no_trans, r_trans.wr_addr, r_trans.wr_data);
            reg_rf[r_trans.wr_addr] = r_trans.wr_data;
        end
        else if (r_trans.rd_en) begin
            if(reg_rf[r_trans.rd_addr] != r_trans.rd_data) begin
                // $error("[SCB-FAIL] #Reg Trans = %0d, Addr = 0x%0h, \n \t Data :: Expected = 0x%0h Actual = 0x%0h",
                //       r_trans.no_trans, r_trans.rd_addr, reg_rf[r_trans.rd_addr], r_trans.rd_data); 
            end
            else if (~r_trans.rd_data_valid) begin
                // $error("[SCB-FAIL] #Reg Trans = %0d, rd_data_valid signal is not asserted", r_trans.no_trans);
            end
            else begin
                // $display("[SCB-PASS] #Reg Trans = %0d, Addr = 0x%0h, \n \t Data :: Expected = 0x%0h Actual = 0x%0h",
                //          r_trans.no_trans, r_trans.rd_addr, reg_rf[r_trans.rd_addr], r_trans.rd_data); 
            end
        end
        no_trans++;
    end
endtask
