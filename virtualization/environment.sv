/*=============================================================================
** Module: environemnet.sv
** Description:
**              program to drive garnet testbench
** Author: Keyi Zhang, Taeyoung Kong
** Change history:  10/25/2020 - Implement the first version
**===========================================================================*/

class Environment;
    typedef enum int {GLB_PCFG_CTRL, GLB_STRM_G2F_CTRL, GLB_STRM_F2G_CTRL} e_glb_ctrl;

    vAxilIfcDriver vifc_axil;
    vProcIfcDriver vifc_proc;

    Kernel kernels[];
    semaphore proc_lock;
    semaphore axil_lock;

    ProcDriver proc_drv;
    AxilDriver axil_drv;

    extern function new(Kernel kernels[], vAxilIfcDriver vifc_axil, vProcIfcDriver vifc_proc);
    extern function void build();
    extern task write_data(Kernel kernel);
    extern task glb_configure(Kernel kernel);
    extern task cgra_configure(Kernel kernel);
    extern task set_interrupt_on();
    extern task wait_interrupt(e_glb_ctrl glb_ctrl, bit[NUM_GLB_TILES-1:0] tile_mask);
    extern task clear_interrupt(e_glb_ctrl glb_ctrl, bit[NUM_GLB_TILES-1:0] tile_mask);
    extern task kernel_test(Kernel kernel);
    extern task read_data(Kernel kernel);
    extern task run();
endclass

function Environment::new(Kernel kernels[], vAxilIfcDriver vifc_axil, vProcIfcDriver vifc_proc);
    this.kernels = kernels;
    this.vifc_axil = vifc_axil;
    this.vifc_proc = vifc_proc;
endfunction

function void Environment::build();
    proc_lock = new(1);
    axil_lock = new(1);
    proc_drv = new(vifc_proc.driver, proc_lock);
    axil_drv = new(vifc_axil.driver, axil_lock);
endfunction

task Environment::write_data(Kernel kernel);
    proc_drv.write_bs(kernel.bs_start_addr, kernel.bitstream_data);
    repeat (10) @(vifc_proc.cbd);
    foreach(kernel.input_data[j]) begin
        proc_drv.write_data(kernel.input_start_addr[j], kernel.input_data[j]);
    end
endtask

task Environment::glb_configure(Kernel kernel);
    axil_drv.config_write(kernel.bs_cfg);
    foreach(kernel.input_cfg[i]) begin
        axil_drv.config_write(kernel.input_cfg[i]);
    end
    foreach(kernel.output_cfg[i]) begin
        axil_drv.config_write(kernel.output_cfg[i]);
    end
    axil_drv.config_write(kernel.tile_cfg);
endtask

task Environment::cgra_configure(Kernel kernel);
    // define variables
    bit [NUM_GLB_TILES-1:0] tile_mask;
    Config cfg;

    cfg = kernel.get_pcfg_start_config();
    axil_drv.write(cfg.addr, cfg.data);
    tile_mask = (1 << kernel.bs_tile);

    wait_interrupt(GLB_PCFG_CTRL, tile_mask);
    clear_interrupt(GLB_PCFG_CTRL, tile_mask);
endtask

task Environment::kernel_test(Kernel kernel);
    bit [NUM_GLB_TILES-1:0] tile_mask;
    Config cfg;
    cfg = kernel.get_strm_start_config();
    axil_drv.write(cfg.addr, cfg.data);
    foreach(kernel.input_tile[i]) begin
        tile_mask |= (1 << kernel.input_tile[i]);
    end

    wait_interrupt(GLB_STRM_F2G_CTRL, tile_mask);
    clear_interrupt(GLB_STRM_F2G_CTRL, tile_mask);
endtask

task Environment::run();
    // wait for reset
    repeat (20) @(vifc_proc.cbd);

    set_interrupt_on();
    foreach(kernels[i]) begin
        automatic int j = i;
        fork
            begin
                write_data(kernels[j]);
                glb_configure(kernels[j]);
                cgra_configure(kernels[j]);
                kernel_test(kernels[j]);
                read_data(kernels[j]);
            end
        join_none
    end
    wait fork;
    repeat (20) @(vifc_axil.cbd);

    foreach(kernels[i]) begin
        kernels[i].compare();
    end

endtask

task Environment::set_interrupt_on();
    axil_drv.write(`GLC_GLOBAL_IER, 3'b111);
    axil_drv.write(`GLC_PAR_CFG_G2F_IER, {NUM_GLB_TILES{1'b1}});
    axil_drv.write(`GLC_STRM_F2G_IER, {NUM_GLB_TILES{1'b1}});
endtask

task Environment::wait_interrupt(e_glb_ctrl glb_ctrl, bit[NUM_GLB_TILES-1:0] tile_mask);
    bit [AXI_ADDR_WIDTH-1:0] addr;
    bit [AXI_DATA_WIDTH-1:0] data;

    // which interrupt
    if (glb_ctrl == GLB_PCFG_CTRL) begin
        addr = `GLC_PAR_CFG_G2F_ISR;
    end
    else if (glb_ctrl == GLB_STRM_G2F_CTRL) begin
        addr = `GLC_STRM_G2F_ISR;
    end
    else begin
        addr = `GLC_STRM_F2G_ISR;
    end

    fork
        begin
            forever begin
                // level sensitive interrupt
                wait(top.interrupt);
                axil_drv.read(addr, data);
                if (&(data | (~tile_mask)) == 1) begin
                    break;
                end
            end
        end
        begin
            repeat (1_000_000) @(vifc_axil.cbd);
            $display("@%0t: %m ERROR: Interrupt wait timeout ", $time);
        end
    join_any
    disable fork;
endtask

task Environment::clear_interrupt(e_glb_ctrl glb_ctrl, bit[NUM_GLB_TILES-1:0] tile_mask);
    bit [AXI_ADDR_WIDTH-1:0] addr;

    // which interrupt
    if (glb_ctrl == GLB_PCFG_CTRL) begin
        addr = `GLC_PAR_CFG_G2F_ISR;
    end
    else if (glb_ctrl == GLB_STRM_G2F_CTRL) begin
        addr = `GLC_STRM_G2F_ISR;
    end
    else begin
        addr = `GLC_STRM_F2G_ISR;
    end

    axil_drv.write(addr, tile_mask);
endtask

task Environment::read_data(Kernel kernel);
    repeat (20) @(vifc_proc.cbd);

    foreach(kernel.output_data[i]) begin
        proc_drv.read_data(kernel.output_start_addr[i], kernel.output_data[i]);
    end

endtask
