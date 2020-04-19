/*=============================================================================
** Module: environment.sv
** Description:
**              environement class
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

class Environment;
    // processor packet generator and driver
    procGenerator   p_gen;
    procDriver      p_drv;

    // mailbox handle
    mailbox         p_gen2drv;

    // event handle
    event           p_drv2gen;

    // processor packet virtual interface
    v_proc_ifc p_vif;

    extern function new(v_proc_ifc p_vif);
    extern function void build();
    extern task run();
endclass

function Environment::new(input v_proc_ifc p_vif);
    // get the interface from test
    this.p_vif = p_vif;
endfunction

function void Environment::build();
    // create the mailbox
    p_gen2drv = new();

    // create generator and driver
    p_gen   = new(p_gen2drv, p_drv2gen);
    p_drv   = new(p_vif.driver, p_gen2drv, p_drv2gen);

endfunction

task Environment::run();
    // number of generators currently running
    int num_gen_running;

    // Wait for resetting
    repeat (100) @(p_vif.cbd);

    // start generator and driver
    fork
        // start processor packet generator
        begin
            num_gen_running++;
            p_gen.run();
            num_gen_running--;
        end
        // start processor packet driver
        p_drv.run();

        // TODO: add other generators and drivers here
    join_none

    // TODO: start monitor

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

