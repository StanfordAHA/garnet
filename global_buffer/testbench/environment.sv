/*=============================================================================
** Module: Environment.sv
** Description:
**              environement class
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

class Environment;
    // Scoreboard
    Scoreboard      scb;

    // processor packet generator, driver, and monitor
    ProcGenerator   p_gen;
    ProcDriver      p_drv;
    ProcMonitor     p_mon;

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
    extern task test();
    extern task post_test();
endclass

function Environment::new(input vProcIfc p_vif);
    // get the interface from test
    this.p_vif = p_vif;
endfunction

function void Environment::build();
    // create the mailbox
    p_gen2drv = new();
    p_mon2scb = new();

    // create generator and driver
    p_gen   = new(p_gen2drv, p_drv2gen);
    p_drv   = new(p_vif.driver, p_gen2drv, p_drv2gen);
    p_mon   = new(p_vif.monitor, p_mon2scb);

    // create Scoreboard
    scb     = new(p_mon2scb);
endfunction

task Environment::test();
    // number of generators currently running
    int num_gen_running;

    // wait for reset
    repeat (100) @(p_vif.cbd);

    // start generator
    fork
        // start processor packet generator
        begin
            num_gen_running++;
            p_gen.run();
            num_gen_running--;
        end
    join_none

    // driver, monitor, and Scoreboard
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

endtask

task Environment::post_test();
    wait(p_gen.repeat_cnt == scb.no_trans);
endtask

task Environment::run();
    test();
    post_test();
    $finish;
endtask
