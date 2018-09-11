import magma
import generator.generator as generator
from common.jtag_type import JTAGType
from generator.configurable import ConfigurationType
from generator.const import Const
from generator.from_magma import FromMagma
from global_controller import global_controller_genesis2


class GlobalController(generator.Generator):
    def __init__(self, addr_width, data_width):
        super().__init__()
        super().__init__()

        self.addr_width = addr_width
        self.data_width = data_width
        self.config_type = ConfigurationType(self.addr_width, self.data_width)

        self.add_ports(
            jtag=JTAGType,
            config=magma.Out(self.config_type),
            clk_in=magma.In(magma.Clock),
            reset_in=magma.In(magma.Reset),
            clk_out=magma.Out(magma.Clock),
            reset_out=magma.Out(magma.Reset),
        )

        wrapper = global_controller_genesis2.gc_wrapper
        type_map = {
            "clk_in": magma.In(magma.Clock),
            "clk_out": magma.Out(magma.Clock),
            "tck": magma.In(magma.Clock),
            "reset_in": magma.In(magma.Reset),
            "reset_out": magma.Out(magma.Reset),
            "trst_n": magma.In(magma.Reset),
        }
        generator = wrapper.generator(mode="declare", type_map=type_map)
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
        self.wire(self.underlying.ports.clk_out, self.ports.clk_out)
        self.wire(self.underlying.ports.reset_out, self.ports.reset_out)

        # TODO(rsetaluri): wire debug read_data into underlying.config_data_in.
        self.wire(Const(magma.bits(0, self.data_width)),
                  self.underlying.ports.config_data_in)

    def name(self):
        return f"GlobalController_{self.addr_width}_{self.data_width}"
