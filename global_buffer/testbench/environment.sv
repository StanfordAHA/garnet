/*=============================================================================
** Module: environment.sv
** Description:
**              environement class
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

class environment;
    // scoreboard
    scoreboard      scb;

    // processor packet generator, driver, and monitor
    procGenerator   p_gen;
    procDriver      p_drv;
    procMonitor     p_mon;

    // mailbox handle
    mailbox         p_gen2drv;
    mailbox         p_mon2scb;

    // event handle
    event           p_drv2gen;

    // processor packet virtual interface
    vProcIfc p_vif;

    extern function new(vProcIfc p_vif);
    extern function void build();
    extern task run();
endclass

function environment::new(input vProcIfc p_vif);
    // get the interface from test
    this.p_vif = p_vif;
endfunction

function void environment::build();
    // create the mailbox
    p_gen2drv = new();

    // create generator and driver
    p_gen   = new(p_gen2drv, p_drv2gen);
    p_drv   = new(p_vif.driver, p_gen2drv, p_drv2gen);
    p_mon   = new(p_vif.monitor, p_mon2scb);

    // create scoreboard
    scb     = new(p_mon2scb);
endfunction

task environment::run();
    // number of generators currently running
    int num_gen_running;

    // start generator
    fork
        // start processor packet generator
        begin
            num_gen_running++;
            p_gen.run();
            num_gen_running--;
        end
    join_none

    // driver, monitor, and scoreboard
    fork
        p_drv.run();
        p_mon.run();
        scb.run();
    join_none

    // Wait for all generators to finish, or time-out
    fork : timeout_block
        wait (num_gen_running == 0);
        begin
            repeat (1_000_000) @(p_vif.cbd);
            $display("@%0t: %m ERROR: Generator timeout ", $time);
        end
    join_any
    disable timeout_block;

    // Wait for the data to flow into monitors and scoreboards
    repeat (1_000) @(p_vif.cbd);

    $finish;
endtask

