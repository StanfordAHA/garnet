/*=============================================================================
** Module: reg_monitor.sv
** Description:
**              class for configuration monitor
** Author: Taeyoung Kong
** Change history:
**  04/20/2020 - Implement first version
**===========================================================================*/
class RegMonitor;

    // declare virtual interface
    vRegIfcMonitor vif; 

    // declare mailbox
    mailbox mon2scb;

    extern function new(vRegIfcMonitor vif, mailbox mon2scb);
    extern task run();
endclass

function RegMonitor::new(vRegIfcMonitor vif, mailbox mon2scb);
    // getting the interface
    this.vif = vif;
    // getting the mailbox handle
    this.mon2scb = mon2scb;
endfunction

task RegMonitor::run();
    forever begin
        // declare transaction
        RegTransaction trans;
        trans = new();

        while(1) begin
            if (vif.cbm.wr_en || vif.cbm.rd_en) begin
                break;
            end
            @(vif.cbm);
        end
        if (vif.cbm.wr_en) begin
            trans.wr_en   = vif.cbm.wr_en;
            trans.wr_addr = vif.cbm.wr_addr;
            trans.wr_data = vif.cbm.wr_data;
            @(vif.cbm);
        end
        else begin
            trans.rd_en   = vif.cbm.rd_en;
            trans.rd_addr = vif.cbm.rd_addr;

            while (1) begin
                @(vif.cbm);
                if (vif.cbm.rd_data_valid) begin
                    break;
                end
            end
            trans.rd_data = vif.cbm.rd_data;
            trans.rd_data_valid = vif.cbm.rd_data_valid;
            @(vif.cbm);
        end
        @(vif.cbm);
        mon2scb.put(trans);
    end
endtask
