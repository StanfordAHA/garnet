/*=============================================================================
** Module: Environment.sv
** Description:
**              environement class
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/
import trans_pkg::*;

class Environment;
    int num_gen_running;

    // Sequence 
    Sequence        seq;

    // Scoreboard
    Scoreboard      scb;

    // processor packet generator, driver, and monitor
    ProcGenerator   p_gen;
    ProcDriver      p_drv;
    ProcMonitor     p_mon;
    RegGenerator    r_gen;
    RegDriver       r_drv;
    RegMonitor      r_mon;
    StrmGenerator   s_gen [NUM_GLB_TILES];
    StrmDriver      s_drv [NUM_GLB_TILES];
    StrmMonitor     s_mon [NUM_GLB_TILES];

    // mailbox handle
    mailbox         p_gen2drv;
    mailbox         p_mon2scb;
    mailbox         r_gen2drv;
    mailbox         r_mon2scb;
    mailbox         s_gen2drv [NUM_GLB_TILES];
    mailbox         s_mon2scb [NUM_GLB_TILES];

    // event handle
    event           p_drv2gen;
    event           r_drv2gen;
    event           s_drv2gen [NUM_GLB_TILES];

    // virtual interface
    vProcIfc        p_vif;
    vRegIfc         r_vif;
    vStrmIfc        s_vif [NUM_GLB_TILES];
    vPcfgIfc        c_vif [NUM_GLB_TILES];

    extern function new(Sequence seq, vProcIfc p_vif, vRegIfc r_vif, vStrmIfc s_vif[], vPcfgIfc c_vif[]);
    extern function void build();
    extern task run();
    extern task test();
    extern task post_test();
endclass

function Environment::new(Sequence seq, vProcIfc p_vif, vRegIfc r_vif, vStrmIfc s_vif[], vPcfgIfc c_vif[]);
    this.num_gen_running = 0;

    // get the sequence from test
    this.seq    = seq;

    // get the interface from test
    this.p_vif  = p_vif;
    this.r_vif  = r_vif;
    this.s_vif = s_vif;
    this.c_vif = c_vif;
endfunction

function void Environment::build();
    // create the mailbox
    p_gen2drv   = new();
    p_mon2scb   = new();
    r_gen2drv   = new();
    r_mon2scb   = new();
    foreach(s_gen2drv[i]) s_gen2drv[i] = new();
    foreach(s_mon2scb[i]) s_mon2scb[i] = new();

    // create generator and driver
    p_gen       = new(p_gen2drv, p_drv2gen);
    p_drv       = new(p_vif.driver, p_gen2drv, p_drv2gen);
    p_mon       = new(p_vif.monitor, p_mon2scb);
    r_gen       = new(r_gen2drv, r_drv2gen);
    r_drv       = new(r_vif.driver, r_gen2drv, r_drv2gen);
    r_mon       = new(r_vif.monitor, r_mon2scb);
    foreach(s_gen[i]) s_gen[i] = new(i, s_gen2drv[i], s_drv2gen[i]);
    foreach(s_drv[i]) s_drv[i] = new(i, s_vif[i].driver, s_gen2drv[i], s_drv2gen[i]);
    foreach(s_mon[i]) s_mon[i] = new(i, s_vif[i].monitor, s_mon2scb[i]);

    // create Scoreboard
    scb         = new(p_mon2scb, r_mon2scb, s_mon2scb);
endfunction

task Environment::test();
    // current transaction
    Transaction cur_trans;
    ProcTransaction cur_trans_p;
    RegTransaction cur_trans_r;
    StrmTransaction cur_trans_s;

    // wait for reset
    repeat (100) @(p_vif.cbd);

    // start scoreboard
    fork
        scb.run();
    join_none

    // start driver and monitor
    fork
        p_drv.run();
        p_mon.run();
        r_drv.run();
        r_mon.run();
    join_none

    foreach(s_drv[i]) begin
        fork
            s_drv[i].run();
        join_none
    end

    foreach(s_mon[i]) begin
        fork
            s_mon[i].run();
        join_none
    end

    fork
        // start generator in sequence
        foreach(seq.trans_q[i]) begin
            cur_trans = seq.trans_q[i];
            if(cur_trans.trans_type == PROC) begin
                $cast(cur_trans_p, cur_trans);
                p_gen.blueprint = cur_trans_p;
                p_gen.run();
            end
            else if (cur_trans.trans_type == REG) begin
                $cast(cur_trans_r, cur_trans);
                r_gen.blueprint = cur_trans_r;
                r_gen.run();
            end
            // else if (cur_trans.trans_type == STRM) begin
            //     $cast(cur_trans_s, cur_trans);
            //     s_gen.blueprint = cur_trans_s;
            //     num_gen_running++;
            //     s_gen.run();
            //     num_gen_running--;
            // end
            // TODO
        end
    join_none

endtask

task Environment::post_test();
    // Wait for all transactions to be checked by scoreboard
    fork : timeout_block
        wait(scb.no_trans == seq.trans_q.size());
        begin
            repeat (1_000_000) @(p_vif.cbd);
            $display("@%0t: %m ERROR: Generator timeout ", $time);
        end
    join_any
    disable timeout_block;
endtask

task Environment::run();
    test();
    post_test();
endtask
