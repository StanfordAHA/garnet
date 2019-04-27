import magma
from gemstone.common.jtag_type import JTAGType
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.const import Const
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.generator import Generator
from . import global_controller_genesis2
from global_buffer.mmio_type import MMIOType


class GlobalController(Generator):
    def __init__(self, addr_width, data_width, soc_addr):
        super().__init__()

        self.addr_width = addr_width
        self.data_width = data_width
        self.soc_addr = soc_addr
        self.config_type = ConfigurationType(self.addr_width, self.data_width)
        self.top_config_type = ConfigurationType(self.soc_addr,
                                                 self.data_width)
        self.glb_config_type = ConfigurationType(self.addr_width,
                                                 self.data_width)

        self.add_ports(
            jtag=JTAGType,
            config=magma.Out(self.config_type),
            read_data_in=magma.In(magma.Bits[self.data_width]),
            top_config=magma.Out(self.top_config_type),
            top_read_data_in=magma.In(magma.Bits[self.data_width]),
            glb_config=magma.Out(self.glb_config_type),
            glb_read_data_in=magma.In(magma.Bits[self.data_width]),
            clk_in=magma.In(magma.Clock),
            reset_in=magma.In(magma.AsyncReset),
            clk_out=magma.Out(magma.Clock),
            reset_out=magma.Out(magma.AsyncReset),
            cgra_start_pulse=magma.Out(magma.Bit),
            cgra_done_pulse=magma.In(magma.Bit),
            config_start_pulse=magma.Out(magma.Bit),
            config_done_pulse=magma.In(magma.Bit),
            soc_ctrl=MMIOType(self.soc_addr, self.data_width),
            soc_interrupt=magma.Out(magma.Bit),
            # TODO: make number of stall domains a param
            stall=magma.Out(magma.Bits[4]),
            glb_stall=magma.Out(magma.Bit),
        )

        wrapper = global_controller_genesis2.gc_wrapper
        generator = wrapper.generator(mode="declare")
        self.underlying = FromMagma(generator())

        self.wire(self.ports.jtag.tdi, self.underlying.ports.tdi)
        self.wire(self.ports.jtag.tdo, self.underlying.ports.tdo)
        self.wire(self.ports.jtag.tms, self.underlying.ports.tms)
        self.wire(self.ports.jtag.tck, self.underlying.ports.tck)
        self.wire(self.ports.jtag.trst_n, self.underlying.ports.trst_n)
        self.wire(self.ports.clk_in, self.underlying.ports.clk_in)
        self.wire(self.ports.reset_in, self.underlying.ports.reset_in)

        self.wire(self.underlying.ports.config_addr_out,
                  self.ports.config.config_addr)
        self.wire(self.underlying.ports.config_data_out,
                  self.ports.config.config_data)
        self.wire(self.underlying.ports.read, self.ports.config.read[0])
        self.wire(self.underlying.ports.write, self.ports.config.write[0])
        self.wire(self.underlying.ports.clk_out, self.ports.clk_out)
        self.wire(self.underlying.ports.reset_out, self.ports.reset_out)
        self.wire(self.underlying.ports.cgra_stalled, self.ports.stall)
        self.wire(self.underlying.ports.glb_stall, self.ports.glb_stall)

        self.wire(self.ports.read_data_in, self.underlying.ports.config_data_in)

        self.wire(self.ports.cgra_start_pulse, self.underlying.ports.cgra_start_pulse)
        self.wire(self.ports.cgra_done_pulse, self.underlying.ports.cgra_done_pulse)
        self.wire(self.ports.config_start_pulse, self.underlying.ports.config_start_pulse)
        self.wire(self.ports.config_done_pulse, self.underlying.ports.config_done_pulse)

        self.wire(self.underlying.ports.top_config_addr_out,
                  self.ports.top_config.config_addr)
        self.wire(self.underlying.ports.top_config_data_out,
                  self.ports.top_config.config_data)
        self.wire(self.underlying.ports.top_read, self.ports.top_config.read[0])
        self.wire(self.underlying.ports.top_write, self.ports.top_config.write[0])
        self.wire(self.ports.top_read_data_in, self.underlying.ports.top_config_data_in)

        self.wire(self.underlying.ports.glb_config_addr_out,
                  self.ports.glb_config.config_addr)
        self.wire(self.underlying.ports.glb_config_data_out,
                  self.ports.glb_config.config_data)
        self.wire(self.underlying.ports.glb_read, self.ports.glb_config.read[0])
        self.wire(self.underlying.ports.glb_write, self.ports.glb_config.write[0])
        self.wire(self.ports.glb_read_data_in, self.underlying.ports.glb_config_data_in)

        self.wire(self.ports.soc_ctrl.wr_en, self.underlying.ports.soc_control_wr_en)
        self.wire(self.ports.soc_ctrl.wr_addr, self.underlying.ports.soc_control_wr_addr)
        self.wire(self.ports.soc_ctrl.wr_data, self.underlying.ports.soc_control_wr_data)
        self.wire(self.ports.soc_ctrl.rd_en, self.underlying.ports.soc_control_rd_en)
        self.wire(self.ports.soc_ctrl.rd_addr, self.underlying.ports.soc_control_rd_addr)
        self.wire(self.ports.soc_ctrl.rd_data, self.underlying.ports.soc_control_rd_data)
        self.wire(self.ports.soc_interrupt, self.underlying.ports.soc_interrupt)


    def name(self):
        return f"GlobalController_{self.addr_width}_{self.data_width}_{self.soc_addr}"
