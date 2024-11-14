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

task AxilDriver::config_write(Config cfg[]);
    foreach (cfg[i]) begin
        write(cfg[i].addr, cfg[i].data);
    end
endtask

task AxilDriver::write(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr, bit [CGRA_AXI_DATA_WIDTH-1:0] data);
    // $display("AXI-Lite Write. Addr: %08h, Data: %08h", addr, data);
    axil_lock.get(1);
    @(vif.cbd);
    vif.cbd.awaddr  <= addr;
    vif.cbd.awvalid <= 1'b1;
    for (int i = 0; i < 100; i++) begin
        if (vif.cbd.awready == 1) break;
        @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    @(vif.cbd);
    vif.cbd.awvalid <= 0;
    @(vif.cbd);
    this.vif.cbd.wdata  <= data;
    this.vif.cbd.wvalid <= 1'b1;
    for (int i = 0; i < 100; i++) begin
        if (this.vif.cbd.wready == 1) break;
        @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    @(vif.cbd);
    this.vif.cbd.wvalid <= 0;
    this.vif.cbd.bready <= 1'b1;
    for (int i = 0; i < 100; i++) begin
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
    for (int i = 0; i < 100; i++) begin
        if (this.vif.cbd.arready == 1) break;
        @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    @(vif.cbd);
    this.vif.cbd.arvalid <= 0;
    @(vif.cbd);
    for (int i = 0; i < 100; i++) begin
        if (this.vif.cbd.rvalid == 1) break;
        @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    data = this.vif.cbd.rdata;
    @(vif.cbd);
    this.vif.cbd.rready <= 0;
    @(vif.cbd);
    // $display("AXI-Lite Read. Addr: %08h, Data: %08h", addr, data);
    axil_lock.put(1);
endtask

