/*=============================================================================
** Module: proc_monitor.sv
** Description:
**              class for processor packet monitor
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

class procMonitor;

    // declare virtual interface
    vProcIfcMonitor vif; 

    // declare mailbox
    mailbox mon2scb;

    extern function new(vProcIfcMonitor vif);
    extern task run();
endclass

function procDriver::new(vProcIfcMonitor vif, mailbox mon2scb);
    // getting the interface
    this.vif = vif;
    // getting the mailbox handle
    this.mon2scb = mon2scb;
endfunction

task procDriver::run();
    forever begin
        // declare transaction
        procTransaction trans;
        trans = new();

        // queue to store wr_strb and wr_data
        bit [BANK_DATA_WIDTH/8-1:0] wr_strb_q[$];
        bit [BANK_DATA_WIDTH-1:0]   wr_data_q[$];
        bit [BANK_DATA_WIDTH-1:0]   rd_data_q[$];
        bit                         rd_data_valid_q[$];

        wait(vif.wr_en || vif.rd_en);
        if (vif.wr_en) begin
            trans.wr_en   = vif.wr_en;
            trans.wr_addr = vif.wr_addr;
            while (vif.wr_en) begin
                wr_strb_q.push_back(vif.wr_strb);
                wr_data_q.push_back(vif.wr_data);
                @(vif.cbm);
            end
            // copy data in queue to transaction
            trans.wr_strb = wr_strb_q;
            trans.wr_data = wr_data_q;
        end
        else begin
            trans.rd_en   = vif.rd_en;
            trans.rd_addr = vif.rd_addr;
            wait(vif.rd_data_valid);
            while (vif.rd_data_valid) begin
                rd_data_q.push_back(vif.rd_data);
                rd_data_valid_q.push_back(vif.rd_data_valid);
                @(vif.cbm);
            end
            // copy data in queue to transaction
            trans.rd_data = rd_data_q;
            trans.rd_data_valid = rd_data_valid_q;
        end
        mon2scb.put(trans);
    end
endtask
