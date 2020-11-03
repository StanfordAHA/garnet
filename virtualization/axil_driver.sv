class AxilDriver;
    vAxilIfcDriver vif;

    extern function new(vAxilIfcDriver vif);
    extern task write(bit[AXI_ADDR_WIDTH-1:0] addr, bit[AXI_DATA_WIDTH-1:0] data);
endclass

function AxilDriver::new(vAxilIfcDriver vif);
    this.vif = vif;
endfunction

task AxilDriver::write(bit[AXI_ADDR_WIDTH-1:0] addr, bit[AXI_DATA_WIDTH-1:0] data);
    @(vif.cbd);
    vif.cbd.awaddr <= addr;
    vif.cbd.awvalid <= 1'b1;
    for (int i=0; i<100; i++) begin
        if (vif.cbd.awready==1) break;
        @(vif.cbd);
    end
    @(vif.cbd);
    vif.cbd.awvalid <= 0;
    @(vif.cbd);
    this.vif.cbd.wdata <= data;
    this.vif.cbd.wvalid <= 1;
    for (int i=0; i<100; i++) begin
        if (this.vif.cbd.wready==1) break;
        @(vif.cbd);
    end
    @(vif.cbd);
    this.vif.cbd.wvalid <= 0;
    this.vif.cbd.bready <= 1;
    for (int i=0; i<100; i++) begin
        if (this.vif.cbd.bvalid == 1) break;
        @(vif.cbd);
    end
    @(vif.cbd);
    this.vif.cbd.bready <= 0;
    @(vif.cbd);
endtask

