/*=============================================================================
** Module: reg_driver.sv
** Description:
**              class for configuration driver
** Author: Taeyoung Kong
** Change history:
**  04/19/2020 - Implement first version
**===========================================================================*/

class RegDriver;

    // declare virtual interface
    vRegIfcDriver vif; 

    // declaring mailbox
    mailbox gen2drv;

    // declare event
    event drv2gen;

    extern function new(vRegIfcDriver vif, mailbox gen2drv, event drv2gen);
    extern task run();
    extern task write(input RegTransaction trans);
    extern task read(input RegTransaction trans);

endclass

function RegDriver::new(vRegIfcDriver vif, mailbox gen2drv, event drv2gen);
    // getting the interface
    this.vif = vif;
    // getting the mailbox handle
    this.gen2drv = gen2drv;
    // getting the event handle
    this.drv2gen = drv2gen;
endfunction

task RegDriver::run();
    // set stall flag to test stalling
    bit stall = 0;

    // initialize ports
    vif.cbd.wr_en       <= 0;
    vif.cbd_n.wr_clk_en   <= 0;
    vif.cbd.wr_addr     <= 0;
    vif.cbd.wr_data     <= 0;
    vif.cbd.rd_en       <= 0;
    vif.cbd_n.rd_clk_en   <= 0;
    vif.cbd.rd_addr     <= 0;

    // drive the transaction items to interface signals 
    forever begin
        RegTransaction trans;
        gen2drv.get(trans);

        if (trans.wr_en) write(trans);
        else             read(trans);
        ->drv2gen;
    end
endtask

task RegDriver::write(input RegTransaction trans);
    // clk enable is set half clk cycle earlier
    @(vif.cbd_n)
    vif.cbd_n.wr_clk_en <= trans.wr_clk_en;

    repeat(2) @(vif.cbd);
    vif.cbd.wr_en   <= trans.wr_en;
    vif.cbd.wr_addr <= trans.wr_addr;
    vif.cbd.wr_data <= trans.wr_data;

    @(vif.cbd);
    vif.cbd.wr_en   <= 0;
    vif.cbd.wr_addr <= 0;
    vif.cbd.wr_data <= 0;

    @(vif.cbd_n)
    vif.cbd_n.wr_clk_en <= 0;

    @(vif.cbd);

endtask

task RegDriver::read(input RegTransaction trans);

    // clk enable is set half clk cycle earlier
    @(vif.cbd_n)
    vif.cbd_n.rd_clk_en <= trans.rd_clk_en;

    repeat(2) @(vif.cbd);
    vif.cbd.rd_en   <= trans.rd_en;
    vif.cbd.rd_addr <= trans.rd_addr;

    fork
        begin
            wait (vif.cbd.rd_data_valid);
            trans.rd_data       <= vif.cbd.rd_data;
            trans.rd_data_valid <= vif.cbd.rd_data_valid;
        end
        begin
            @(vif.cbd);
            vif.cbd.rd_en   <= 0;
            vif.cbd.rd_addr <= 0;

            @(vif.cbd_n)
            vif.cbd_n.rd_clk_en <= 0;
        end
    join

    @(vif.cbd);

endtask

