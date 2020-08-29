/*=============================================================================
** Module: proc_monitor.sv
** Description:
**              class for processor packet monitor
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/
class ProcMonitor;

    // declare virtual interface
    vProcIfcMonitor vif; 

    // declare mailbox
    mailbox mon2scb;

    extern function new(vProcIfcMonitor vif, mailbox mon2scb);
    extern task run();
endclass

function ProcMonitor::new(vProcIfcMonitor vif, mailbox mon2scb);
    // getting the interface
    this.vif = vif;
    // getting the mailbox handle
    this.mon2scb = mon2scb;
endfunction

task ProcMonitor::run();
    // queue to store wr_strb and wr_data
    bit [BANK_DATA_WIDTH/8-1:0] wr_strb_q[$];
    bit [BANK_DATA_WIDTH-1:0]   wr_data_q[$];
    bit [BANK_DATA_WIDTH-1:0]   rd_data_q[$];
    bit                         rd_data_valid_q[$];

    forever begin
        // declare transaction
        ProcTransaction trans;
        trans = new();

        // empty queue
        wr_strb_q       = {};
        wr_data_q       = {};
        rd_data_q       = {};
        rd_data_valid_q = {};

        wait(vif.cbm.wr_en || vif.cbm.rd_en);
        if (vif.cbm.wr_en) begin
            trans.wr_en   = vif.cbm.wr_en;
            trans.wr_addr = vif.cbm.wr_addr;
            while (vif.cbm.wr_en) begin
                wr_strb_q.push_back(vif.cbm.wr_strb);
                wr_data_q.push_back(vif.cbm.wr_data);
                @(vif.cbm);
            end
            // copy data in queue to transaction
            trans.wr_strb = wr_strb_q;
            trans.wr_data = wr_data_q;
        end
        else begin
            trans.rd_en   = vif.cbm.rd_en;
            trans.rd_addr = vif.cbm.rd_addr;
            wait(vif.cbm.rd_data_valid);
            while (vif.cbm.rd_data_valid) begin
                rd_data_q.push_back(vif.cbm.rd_data);
                rd_data_valid_q.push_back(vif.cbm.rd_data_valid);
                @(vif.cbm);
            end
            trans.rd_data = rd_data_q;
            trans.rd_data_valid = rd_data_valid_q;
        end
        mon2scb.put(trans);
    end
endtask
