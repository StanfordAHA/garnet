/*=============================================================================
** Module: proc_generator.sv
** Description:
**              class for processor packet generator
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

class procGenerator;

    // declare processor packet transaction class
    procTransaction trans;

    // declaring mailbox
    mailbox gen2drv;

    // event
    event drv2gen;

    extern function new(mailbox gen2drv, event drv2gen);
    extern task run();

endclass

function procGenerator::new(mailbox gen2drv, event drv2gen);
    this.gen2drv   = gen2drv;
    this.drv2gen   = drv2gen;
endfunction

task procGenerator::run();
    trans = new();
    if (!trans.randomize()) $fatal("Proc Gen:: trans randomization failed");
    if (trans.rd_en) begin
        trans.allocate();
    end
    gen2drv.put(trans);
    // waiting for driver to finish with it
    @drv2gen;
endtask

