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
    int st_tile;
    int ld_tile;
    // queue to store wr_strb and wr_data
    bit [CGRA_DATA_WIDTH-1:0]   ld_data_q[$];
    bit [CGRA_DATA_WIDTH-1:0]   st_data_q[$];

endtask
