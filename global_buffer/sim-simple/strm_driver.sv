/*=============================================================================
** Module: strm_driver.sv
** Description:
**              class for stream packet driver
** Author: Taeyoung Kong
** Change history:
**  04/20/2020 - Implement first version
**===========================================================================*/

class StrmDriver;
    int id;

    // declare virtual interface
    vStrmIfcDriver vif; 

    // declaring mailbox
    mailbox gen2drv;

    // declare event
    event drv2gen;

    extern function new(int id, vStrmIfcDriver vif, mailbox gen2drv, event drv2gen);
    extern task run();
    extern task store(input StrmTransaction trans);
    extern task load(input StrmTransaction trans);

endclass

function StrmDriver::new(int id, vStrmIfcDriver vif, mailbox gen2drv, event drv2gen);
    this.id = id;
    // getting the interface
    this.vif = vif;
    // getting the mailbox handle
    this.gen2drv = gen2drv;
    // getting the event handle
    this.drv2gen = drv2gen;
endfunction

task StrmDriver::run();
    // set stall flag to test stalling
    bit stall = 0;

    // initialize ports
    vif.cbd.strm_start_pulse    <= 0;
    vif.cbd.data_f2g            <= 0;
    vif.cbd.data_valid_f2g      <= 0;

    // drive the transaction items to interface signals 
    forever begin
        StrmTransaction trans;
        gen2drv.get(trans);

        fork
            begin
                if (trans.ld_on) load(trans);
            end
            begin
                if (trans.st_on) store(trans);
            end
        join
        ->drv2gen;
    end
endtask

task StrmDriver::store(input StrmTransaction trans);
    int i, j;
    bit valid;
    i = 0;
    j = trans.st_length;

    @(vif.cbd);
    while (i != j) begin
        //valid = $urandom_range(0, 1);
        valid = 1;
        if (valid == 1) begin
            vif.cbd.data_valid_f2g <= 1;
            vif.cbd.data_f2g <= trans.st_data[i];
            i++;
        end
        else begin
            vif.cbd.data_valid_f2g <= 0;
        end
        @(vif.cbd);
    end
    vif.cbd.data_valid_f2g <= 0;

endtask

task StrmDriver::load(input StrmTransaction trans);
    int j;
    j = trans.ld_length;

    @(vif.cbd);
    vif.cbd.strm_start_pulse <= 1;
    @(vif.cbd);
    vif.cbd.strm_start_pulse <= 0;
    
    wait (vif.cbd.data_valid_g2f);
    for (int i=0; i<j; i++) begin
        assert (vif.cbd.data_valid_g2f == 1);
        trans.ld_data[i] = vif.cbd.data_g2f;
        @(vif.cbd);
    end

endtask
