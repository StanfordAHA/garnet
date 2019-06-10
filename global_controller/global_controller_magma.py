import magma
from gemstone.common.jtag_type import JTAGType
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.generator import Generator
from . import global_controller_genesis2
from global_controller.axi4_type import AXI4SlaveType


class GlobalController(Generator):
    def __init__(self, addr_width, data_width, axi_addr_width):
        super().__init__()

        self.addr_width = addr_width
        self.data_width = data_width
        self.axi_addr_width = axi_addr_width
        self.config_type = ConfigurationType(self.addr_width, self.data_width)
        self.axi_config_type = ConfigurationType(self.axi_addr_width,
                                                 self.data_width)

        self.add_ports(
            clk_in=magma.In(magma.Clock),
            reset_in=magma.In(magma.AsyncReset),

            clk_out=magma.Out(magma.Clock),
            reset_out=magma.Out(magma.AsyncReset),
            stall=magma.Out(magma.Bits[1]),
            glb_stall=magma.Out(magma.Bit),

            cgra_start_pulse=magma.Out(magma.Bit),
            cgra_done_pulse=magma.In(magma.Bit),
            cgra_soft_reset=magma.Out(magma.Bit),

            config_start_pulse=magma.Out(magma.Bit),
            config_done_pulse=magma.In(magma.Bit),

            glb_config=magma.Out(self.axi_config_type),
            glb_read_data_in=magma.In(magma.Bits[self.data_width]),
            glb_sram_config=magma.Out(self.config_type),
            glb_sram_read_data_in=magma.In(magma.Bits[self.data_width]),
            config=magma.Out(self.config_type),
            read_data_in=magma.In(magma.Bits[self.data_width]),

            jtag=JTAGType,

            axi4_ctrl=AXI4SlaveType(self.axi_addr_width, self.data_width),
        )

        wrapper = global_controller_genesis2.gc_wrapper
        generator = wrapper.generator(mode="declare")
        self.underlying = FromMagma(generator())

        # wire clk and reset
        self.wire(self.ports.clk_in, self.underlying.ports.clk_in)
        self.wire(self.ports.reset_in, self.underlying.ports.reset_in)

        # cgra control signals
        self.wire(self.underlying.ports.clk_out, self.ports.clk_out)
        self.wire(self.underlying.ports.reset_out, self.ports.reset_out)
        self.wire(self.underlying.ports.cgra_stalled, self.ports.stall)
        self.wire(self.underlying.ports.glb_stall, self.ports.glb_stall)
        self.wire(self.ports.cgra_start_pulse,
                  self.underlying.ports.cgra_start_pulse)
        self.wire(self.ports.cgra_done_pulse,
                  self.underlying.ports.cgra_done_pulse)
        self.wire(self.ports.cgra_soft_reset,
                  self.underlying.ports.cgra_soft_reset)

        # fast reconfiguration interface
        self.wire(self.ports.config_start_pulse,
                  self.underlying.ports.config_start_pulse)
        self.wire(self.ports.config_done_pulse,
                  self.underlying.ports.config_done_pulse)

        # glb configuration interface
        self.wire(self.underlying.ports.glb_config_addr_out,
                  self.ports.glb_config.config_addr)
        self.wire(self.underlying.ports.glb_config_data_out,
                  self.ports.glb_config.config_data)
        self.wire(self.underlying.ports.glb_read,
                  self.ports.glb_config.read[0])
        self.wire(self.underlying.ports.glb_write,
                  self.ports.glb_config.write[0])
        self.wire(self.ports.glb_read_data_in,
                  self.underlying.ports.glb_config_data_in)

        # glb sram configuration interface
        self.wire(self.underlying.ports.glb_sram_config_addr_out,
                  self.ports.glb_sram_config.config_addr)
        self.wire(self.underlying.ports.glb_sram_config_data_out,
                  self.ports.glb_sram_config.config_data)
        self.wire(self.underlying.ports.glb_sram_read,
                  self.ports.glb_sram_config.read[0])
        self.wire(self.underlying.ports.glb_sram_write,
                  self.ports.glb_sram_config.write[0])
        self.wire(self.ports.glb_sram_read_data_in,
                  self.underlying.ports.glb_sram_config_data_in)

        # cgra configuration interface
        self.wire(self.underlying.ports.config_addr_out,
                  self.ports.config.config_addr)
        self.wire(self.underlying.ports.config_data_out,
                  self.ports.config.config_data)
        self.wire(self.underlying.ports.read,
                  self.ports.config.read[0])
        self.wire(self.underlying.ports.write,
                  self.ports.config.write[0])
        self.wire(self.ports.read_data_in,
                  self.underlying.ports.config_data_in)

        # axi4-lite slave interface
        self.wire(self.ports.axi4_ctrl.awaddr, self.underlying.ports.AWADDR)
        self.wire(self.ports.axi4_ctrl.awvalid, self.underlying.ports.AWVALID)
        self.wire(self.ports.axi4_ctrl.awready, self.underlying.ports.AWREADY)
        self.wire(self.ports.axi4_ctrl.wdata, self.underlying.ports.WDATA)
        self.wire(self.ports.axi4_ctrl.wvalid, self.underlying.ports.WVALID)
        self.wire(self.ports.axi4_ctrl.wready, self.underlying.ports.WREADY)
        self.wire(self.ports.axi4_ctrl.araddr, self.underlying.ports.ARADDR)
        self.wire(self.ports.axi4_ctrl.arvalid, self.underlying.ports.ARVALID)
        self.wire(self.ports.axi4_ctrl.arready, self.underlying.ports.ARREADY)
        self.wire(self.ports.axi4_ctrl.rdata, self.underlying.ports.RDATA)
        self.wire(self.ports.axi4_ctrl.rresp, self.underlying.ports.RRESP)
        self.wire(self.ports.axi4_ctrl.rvalid, self.underlying.ports.RVALID)
        self.wire(self.ports.axi4_ctrl.rready, self.underlying.ports.RREADY)
        self.wire(self.ports.axi4_ctrl.interrupt,
                  self.underlying.ports.interrupt)

        # jtag interface signals
        self.wire(self.ports.jtag.tdi, self.underlying.ports.tdi)
        self.wire(self.ports.jtag.tdo, self.underlying.ports.tdo)
        self.wire(self.ports.jtag.tms, self.underlying.ports.tms)
        self.wire(self.ports.jtag.tck, self.underlying.ports.tck)
        self.wire(self.ports.jtag.trst_n, self.underlying.ports.trst_n)

    def name(self):
        return f"GlobalController_{self.addr_width}_{self.data_width}"
