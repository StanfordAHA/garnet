/*=============================================================================
** Module: reg_generator.sv
** Description:
**              class for configuration generator
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

class RegGenerator;

    // declare processor packet transaction class
    RegTransaction blueprint, trans;

    // declaring mailbox
    mailbox gen2drv;

    // event
    event drv2gen;

    extern function new(mailbox gen2drv, event drv2gen);
    extern task run();

endclass

function RegGenerator::new(mailbox gen2drv, event drv2gen);
    this.gen2drv = gen2drv;
    this.drv2gen = drv2gen;
endfunction

task RegGenerator::run();
    if (!blueprint.randomize()) $fatal("Reg Gen:: trans randomization failed");
    blueprint.post_randomize();
    $cast(trans, blueprint.copy());

    // print transaction info
`ifdef DEBUG
    trans.display();
`endif

    // increase the number of transaction
    trans.no_trans++;

    gen2drv.put(trans);

    // waiting for driver to finish with it
    @drv2gen;
endtask

