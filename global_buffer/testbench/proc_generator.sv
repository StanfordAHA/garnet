/*=============================================================================
** Module: proc_generator.sv
** Description:
**              class for processor packet generator
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

class ProcGenerator;

    // declare processor packet transaction class
    ProcTransaction blueprint, trans;

    // declaring mailbox
    mailbox gen2drv;

    // event
    event drv2gen;

    // repeat count to specify number of items to generate
    int repeat_cnt;

    extern function new(mailbox gen2drv, event drv2gen);
    extern task run();

endclass

function ProcGenerator::new(mailbox gen2drv, event drv2gen);
    this.gen2drv   = gen2drv;
    this.drv2gen   = drv2gen;
endfunction

task ProcGenerator::run();
    int iter = 0;
    repeat(repeat_cnt) begin
        if (!blueprint.randomize()) $fatal("Proc Gen:: trans randomization failed");
        blueprint.post_randomize();
        $cast(trans, blueprint.copy());
        $display("Generation #%0d starts", iter);
        $display("Transaction info \n \t wr_en: %0d, wr_addr: 0x%0h, rd_en: %0d, rd_addr: 0x%0h, length: %0d",
                 trans.wr_en, trans.wr_addr, trans.rd_en, trans.rd_addr, trans.length);
        gen2drv.put(trans);
        // waiting for driver to finish with it
        @drv2gen;
        iter++;
    end
endtask

