/*=============================================================================
** Module: proc_driver.sv
** Description:
**              class for processor packet driver
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

class ProcDriver;

    // declare virtual interface
    vProcIfcDriver vif; 

    // declaring mailbox
    mailbox gen2drv;

    // declare event
    event drv2gen;

    extern function new(vProcIfcDriver vif, mailbox gen2drv, event drv2gen);
    extern task run();
    extern task write(input ProcTransaction trans);
    extern task read(input ProcTransaction trans);

endclass

function ProcDriver::new(vProcIfcDriver vif, mailbox gen2drv, event drv2gen);
    // getting the interface
    this.vif = vif;
    // getting the mailbox handle
    this.gen2drv = gen2drv;
    // getting the event handle
    this.drv2gen = drv2gen;
endfunction

task ProcDriver::run();
    // set stall flag to test stalling
    bit stall = 0;

    // initialize ports
    vif.cbd.wr_en   <= 0;
    vif.cbd.wr_strb <= 0;
    vif.cbd.wr_addr <= 0;
    vif.cbd.wr_data <= 0;
    vif.cbd.rd_en   <= 0;
    vif.cbd.rd_addr <= 0;

    // drive the transaction items to interface signals 
    forever begin
        ProcTransaction trans;
        gen2drv.get(trans);

        if (trans.wr_en) write(trans);
        else             read(trans);
        ->drv2gen;
    end
endtask

task ProcDriver::write(input ProcTransaction trans);
    int j;
    j = trans.length;

    @(vif.cbd);
    for (int i=0; i<j; i++) begin
        vif.cbd.wr_en   <= trans.wr_en;
        vif.cbd.wr_strb <= trans.wr_strb[i];
        // address increases by 8 every write
        vif.cbd.wr_addr <= (trans.wr_addr + (2**BANK_BYTE_OFFSET)*i);
        vif.cbd.wr_data <= trans.wr_data[i];
        @(vif.cbd);
    end

    vif.cbd.wr_en   <= 0;
    vif.cbd.wr_strb <= 0;
    vif.cbd.wr_addr <= 0;
    vif.cbd.wr_data <= 0;

endtask

task ProcDriver::read(input ProcTransaction trans);
    int j;
    j = trans.length;

    fork
        begin
            @(vif.cbd);
            for (int i=0; i<j; i++) begin
                vif.cbd.rd_en   <= trans.rd_en;
                // address increases by 8 every write
                vif.cbd.rd_addr <= (trans.rd_addr + (2**BANK_BYTE_OFFSET)*i);
                @(vif.cbd);
            end
            vif.cbd.rd_en   <= 0;
            vif.cbd.rd_addr <= 0;
        end
        begin
            for (int i=0; i<j; i++) begin
                wait (vif.cbd.rd_data_valid);
                trans.rd_data[i] = vif.cbd.rd_data;
                trans.rd_data_valid[i] = vif.cbd.rd_data_valid;
                @(vif.cbd);
            end
        end
    join


endtask

