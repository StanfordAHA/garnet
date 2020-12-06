/*=============================================================================
** Module: Scoreboard.sv
** Description:
**              Scoreboard class
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

class Scoreboard;

    // create mailbox handle
    mailbox p_mon2scb;
    mailbox r_mon2scb;
    mailbox m_mon2scb;
    mailbox s_mon2scb [NUM_GLB_TILES];

    // used to count the number of transactions
    int no_trans;

    // global_buffer array
    bit [BANK_DATA_WIDTH-1:0] mem [2**GLB_ADDR_WIDTH-BANK_DATA_WIDTH/8];

    // global_buffer config register file
    bit [AXI_DATA_WIDTH-1:0] reg_rf [2**AXI_ADDR_WIDTH];

    extern function new(mailbox p_mon2scb, mailbox r_mon2scb, mailbox s_mon2scb[], mailbox m_mon2scb);
    extern task run();
    extern task proc_run();
    extern task strm_run(int i);
    extern task reg_run();
    extern task sram_run();

endclass

function Scoreboard::new(mailbox p_mon2scb, mailbox r_mon2scb, mailbox s_mon2scb[], mailbox m_mon2scb);
    // no_trans
    no_trans = 0;

    // getting the mailbox handles from environment
    this.p_mon2scb = p_mon2scb;
    this.r_mon2scb = r_mon2scb;
    this.s_mon2scb = s_mon2scb;
    this.m_mon2scb = m_mon2scb;

    // initialize to zero
    foreach(mem[i])     mem[i] = 0;
    foreach(reg_rf[i])  reg_rf[i] = 0;
endfunction

task Scoreboard::run();
    fork
        proc_run();
        reg_run();
        sram_run();
    join_none
    for(int i=0; i<NUM_GLB_TILES; i++) begin
        fork
            int j = i;
            strm_run(j);
        join_none
    end
endtask

task Scoreboard::proc_run();
    forever begin
        ProcTransaction p_trans;
        p_mon2scb.get(p_trans);
        if(p_trans.wr_en) begin
            foreach(p_trans.wr_data[i]) begin
                if(p_trans.wr_strb[i]) begin
                    assert (p_trans.wr_addr % 8 == 0);
                    mem[p_trans.wr_addr+8*i] = p_trans.wr_data[i];
                    `ifdef DEBUG
                        $display("[SCB-LOG] PROC WRITE :: Addr = 0x%0h, \tData = 0x%0h",
                                 p_trans.wr_addr+8*i, p_trans.wr_data[i]); 
                    `endif
                end
            end
        end
        else if (p_trans.rd_en) begin
            foreach(p_trans.rd_data[i]) begin
                assert (p_trans.rd_addr % 8 == 0);
                if(mem[p_trans.rd_addr+8*i] != p_trans.rd_data[i]) begin
                    $error("[SCB-FAIL] #Trans = %0d, Addr = 0x%0h, \n \t Data :: Expected = 0x%0h Actual = 0x%0h",
                          p_trans.no_trans, p_trans.rd_addr+8*i, mem[p_trans.rd_addr+8*i], p_trans.rd_data[i]); 
                end
                else if (~p_trans.rd_data_valid[i]) begin
                    $error("[SCB-FAIL] #Trans = %0d, rd_data_valid signal is not asserted", p_trans.no_trans);
                end
                else begin
                    `ifdef DEBUG
                        $display("[SCB-LOG] Addr = 0x%0h, \n \t Data :: Expected = 0x%0h Actual = 0x%0h",
                                 p_trans.rd_addr+8*i, mem[p_trans.rd_addr+8*i], p_trans.rd_data[i]); 
                    `endif
                end
            end
            $display("[SCB-PASS] Transaction type: %s READ \n \
                     size: %0d Bytes, start_addr: 0x%0h \n",
                     p_trans.trans_type.name(), p_trans.length*BANK_DATA_WIDTH/8, p_trans.rd_addr);
        end
        no_trans++;
    end
endtask

task Scoreboard::strm_run(int i);
    forever begin
        StrmTransaction s_trans;
        this.s_mon2scb[i].get(s_trans);
        if (s_trans.st_on) begin
            if (reg_rf[(i<<8)+0][9:8] == 2'b01) begin
                bit[GLB_ADDR_WIDTH-1:0] st_start_addr = reg_rf[(i<<8)+'hC][GLB_ADDR_WIDTH-1:0];
                foreach(s_trans.st_data[k]) begin
                    int m = k / 4;
                    int n = k % 4;
                    mem[(st_start_addr >> 3) + m][16*n+:16] = s_trans.st_data[k];
                    `ifdef DEBUG
                        $display("[SCB-LOG] STRM WRITE 2Bytes :: Addr = 0x%0h, \tData = 0x%0h",
                                 st_start_addr+2*k, s_trans.st_data[k]); 
                    `endif
                end
            end
        end
        else begin
            if (reg_rf[(i<<8)+0][7:6] == 2'b01) begin
                bit[GLB_ADDR_WIDTH-1:0] ld_start_addr = reg_rf[(i<<8)+'h3C][GLB_ADDR_WIDTH-1:0];
                bit[20:0] ld_length = reg_rf[(i<<8)+'h44][20:0];
                for (int k=0; k<ld_length; k++) begin
                    int m = k / 4;
                    int n = k % 4;
                    assert (s_trans.ld_data[k] == mem[(ld_start_addr >> 3)+m][16*n+:16])
                    else    $error("[SCB-FAIL] STRM READ 2Bytes :: Addr = 0x%0h, \tData :: Expected = 0x%0h Actual = 0x%0h",
                                   ld_start_addr+2*k, mem[(ld_start_addr >> 3)+m][16*n+:16], s_trans.ld_data[k]); 
                    `ifdef DEBUG
                        $display("[SCB-LOG] STRM READ 2Bytes :: Addr = 0x%0h, \tData = 0x%0h",
                                 ld_start_addr+2*k, s_trans.ld_data[k]); 
                    `endif
                end
            end
        end
        no_trans++;
    end
endtask

task Scoreboard::sram_run();
    forever begin
        RegTransaction  m_trans;
        m_mon2scb.get(m_trans);
        if(m_trans.wr_en) begin
            $display("[SRAM-WRITE] #SRAM Trans = %0d, Addr = 0x%0h, Data 0x%0h", m_trans.no_trans, m_trans.wr_addr, m_trans.wr_data);
            if (m_trans.wr_addr % 8 == 0) begin
                mem[m_trans.wr_addr][31:0] = m_trans.wr_data;
            end else begin
                mem[m_trans.wr_addr][63:32] = m_trans.wr_data;
            end
        end
        else if (m_trans.rd_en) begin
            if(mem[m_trans.rd_addr] != m_trans.rd_data) begin
                $error("[SCB-FAIL] #SRAM Trans = %0d, Addr = 0x%0h, \n \t Data :: Expected = 0x%0h Actual = 0x%0h",
                      m_trans.no_trans, m_trans.rd_addr, mem[m_trans.rd_addr], m_trans.rd_data);
            end
            else if (~m_trans.rd_data_valid) begin
                $error("[SCB-FAIL] #SRAM Trans = %0d, rd_data_valid signal is not asserted", m_trans.no_trans);
            end
            else begin
                $display("[SCB-PASS] #Reg Trans = %0d, Addr = 0x%0h, \n \t Data :: Expected = 0x%0h Actual = 0x%0h",
                         m_trans.no_trans, m_trans.rd_addr, mem[m_trans.rd_addr], m_trans.rd_data);
            end
        end
        no_trans++;
    end
endtask

task Scoreboard::reg_run();
    forever begin
        RegTransaction  r_trans;
        r_mon2scb.get(r_trans);
        if(r_trans.wr_en) begin
            $display("[REG-WRITE] #Reg Trans = %0d, Addr = 0x%0h, Data 0x%0h", r_trans.no_trans, r_trans.wr_addr, r_trans.wr_data);
            reg_rf[r_trans.wr_addr] = r_trans.wr_data;
        end
        else if (r_trans.rd_en) begin
            if(reg_rf[r_trans.rd_addr] != r_trans.rd_data) begin
                $error("[SCB-FAIL] #Reg Trans = %0d, Addr = 0x%0h, \n \t Data :: Expected = 0x%0h Actual = 0x%0h",
                      r_trans.no_trans, r_trans.rd_addr, reg_rf[r_trans.rd_addr], r_trans.rd_data);
            end
            else if (~r_trans.rd_data_valid) begin
                $error("[SCB-FAIL] #Reg Trans = %0d, rd_data_valid signal is not asserted", r_trans.no_trans);
            end
            else begin
                $display("[SCB-PASS] #Reg Trans = %0d, Addr = 0x%0h, \n \t Data :: Expected = 0x%0h Actual = 0x%0h",
                         r_trans.no_trans, r_trans.rd_addr, reg_rf[r_trans.rd_addr], r_trans.rd_data);
            end
        end
        no_trans++;
    end
endtask
