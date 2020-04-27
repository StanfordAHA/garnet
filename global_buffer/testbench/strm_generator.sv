/*=============================================================================
** Module: strm_generator.sv
** Description:
**              class for streaming packet generator
** Author: Taeyoung Kong
** Change history:
**  04/21/2020 - Implement first version
**===========================================================================*/

class StrmGenerator;
    int id;

    // declare processor packet transaction class
    StrmTransaction blueprint, trans;

    // declaring mailbox
    mailbox gen2drv;

    // event
    event drv2gen;

    extern function new(int id, mailbox gen2drv, event drv2gen);
    extern task run();

endclass

function StrmGenerator::new(int id, mailbox gen2drv, event drv2gen);
    this.id = id;
    this.gen2drv = gen2drv;
    this.drv2gen = drv2gen;
endfunction

task StrmGenerator::run();
    if (!blueprint.randomize()) $fatal("Strm Gen:: trans randomization failed");
    blueprint.post_randomize();
    $cast(trans, blueprint.copy());

    // print transaction info
    trans.display();

    // increase the number of transaction
    trans.no_trans++;

    gen2drv.put(trans);

    // waiting for driver to finish with it
    @drv2gen;

endtask

