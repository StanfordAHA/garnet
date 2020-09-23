/*=============================================================================
** Module: strm_monitor.sv
** Description:
**              class for streaming packet monitor
** Author: Taeyoung Kong
** Change history:
**  04/21/2020 - Implement first version
**===========================================================================*/
class StrmMonitor;
    int id;

    // declare virtual interface
    vStrmIfcMonitor vif; 

    // declare mailbox
    mailbox mon2scb;

    extern function new(int id, vStrmIfcMonitor vif, mailbox mon2scb);
    extern task run();
endclass

function StrmMonitor::new(int id, vStrmIfcMonitor vif, mailbox mon2scb);
    this.id = id;
    // getting the interface
    this.vif = vif;
    // getting the mailbox handle
    this.mon2scb = mon2scb;
endfunction

task StrmMonitor::run();
    // queue to store wr_strb and wr_data
    bit [CGRA_DATA_WIDTH-1:0]   ld_data_q[$];
    bit [CGRA_DATA_WIDTH-1:0]   st_data_q[$];

    forever begin
        // declare transaction
        StrmTransaction trans;
        trans = new();

        // empty queue
        ld_data_q       = {};
        st_data_q       = {};

        wait(vif.cbm.data_valid_f2g || vif.cbm.data_valid_g2f);
        if (vif.cbm.data_valid_f2g) begin
            trans.st_on = 1;
            while (!vif.cbm.strm_f2g_interrupt) begin
                if (vif.cbm.data_valid_f2g) begin
                    st_data_q.push_back(vif.cbm.data_f2g);
                    trans.st_length++;
                end
                @(vif.cbm);
            end
        end
        else begin
            trans.ld_on = 1;
            @(vif.cbm);
            while (!vif.cbm.strm_g2f_interrupt) begin
                ld_data_q.push_back(vif.cbm.data_g2f);
                trans.ld_length++;
                @(vif.cbm);
            end
        end
        trans.ld_data = ld_data_q;
        trans.st_data = st_data_q;
        mon2scb.put(trans);
    end
endtask
