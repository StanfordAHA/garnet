`define DBG_AXILDRIVER 0  // Set to '1' for debugging

// If protocol is broken, can shorten SLAVE_WAIT timeout for debugging (10 is a good number)
`define SLAVE_WAIT 100

// (VERILATOR PREP; NOT USED YET) ======================================================
// Can use same global addr and data for everybody because there are only three forks:
// - one in wait_interrupt has a mem read, but
//   - addr is same for all forks, and
//   - data keeps getting overwritten, but we only care about the last one
// - one in Env_run() is disabled and throws an error if anyone ever tries to use it;
// - one in ProcDriver_read_data() does not use addr/data for reads

bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
bit [CGRA_AXI_DATA_WIDTH-1:0] data;

class AxilDriver;
    vAxilIfcDriver vif;
    semaphore axil_lock;

    extern function new(vAxilIfcDriver vif, semaphore axil_lock);
    extern task config_write(Config cfg[]);
    extern task write(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr, bit [CGRA_AXI_DATA_WIDTH-1:0] data);
    extern task read(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr,
                     ref bit [CGRA_AXI_DATA_WIDTH-1:0] data);
endclass

function AxilDriver::new(vAxilIfcDriver vif, semaphore axil_lock);
    this.vif = vif;
    this.axil_lock = axil_lock;
endfunction

Config AxilDriver_cfg[];
task AxilDriver::config_write(Config cfg[]);
    foreach (cfg[i]) begin
        write(cfg[i].addr, cfg[i].data);
    end
endtask

task AxilDriver::write(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr, bit [CGRA_AXI_DATA_WIDTH-1:0] data);
    if (`DBG_AXILDRIVER) $display("[%0t] AXI-Lite Write. Addr: %08h, Data: %08h", $time, addr, data);

    // Note: "slave not ready" timout will occur b/c awready stays false until data is read (below)
    // awready advances controller state from WAIT(0) to WR_REQ_GLC(1)

    axil_lock.get(1);
    @(vif.cbd);
    vif.cbd.awaddr  <= addr;
    vif.cbd.awvalid <= 1'b1;

    // FIXME?? seems like this should happen BEFORE setting awvalid etc. above? First ready, then valid?
    for (int i = 0; i < `SLAVE_WAIT; i++) begin
        if (vif.cbd.awready == 1) break;
        @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    @(vif.cbd);
    vif.cbd.awvalid <= 0;
    @(vif.cbd);
    // Axi controller should now be in state 1 (WR_REQ_GLC==1, see glc_axi_ctrl.sv) // 132ns
    this.vif.cbd.wdata  <= data;
    this.vif.cbd.wvalid <= 1'b1;
    // Axi controller should now be in state 3 (WR_WAIT)  // 132ns
    // Then, after one cycle, on to state 4 (WR_RESP)     // 133ns
    // where it stays until wr_wait_cnt counts from clog2(14) down to zero
    for (int i = 0; i < `SLAVE_WAIT; i++) begin
        if (this.vif.cbd.wready == 1) break;
        @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    @(vif.cbd);
    this.vif.cbd.wvalid <= 0;
    this.vif.cbd.bready <= 1'b1;
    for (int i = 0; i < `SLAVE_WAIT; i++) begin
        if (this.vif.cbd.bvalid == 1) break;
        @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    @(vif.cbd);
    this.vif.cbd.bready <= 0;
    @(vif.cbd);
    axil_lock.put(1);
endtask

task AxilDriver::read(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr,
                      ref bit [CGRA_AXI_DATA_WIDTH-1:0] data);
    axil_lock.get(1);
    @(vif.cbd);
    this.vif.cbd.araddr  <= addr;
    this.vif.cbd.arvalid <= 1'b1;
    this.vif.cbd.rready  <= 1;
    for (int i = 0; i < `SLAVE_WAIT; i++) begin
        if (this.vif.cbd.arready == 1) break;
        @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    @(vif.cbd);
    this.vif.cbd.arvalid <= 0;
    @(vif.cbd);
    for (int i = 0; i < `SLAVE_WAIT; i++) begin
        if (this.vif.cbd.rvalid == 1) break;
        @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    data = this.vif.cbd.rdata;
    @(vif.cbd);
    this.vif.cbd.rready <= 0;
    @(vif.cbd);
    if (`DBG_AXILDRIVER) $display("[%0t] AXI-Lite Read. Addr: %08h, Data: %08h", $time, addr, data);
    axil_lock.put(1);
endtask

