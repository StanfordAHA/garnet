import generator
import magma
from jtag_type import JTAGType
from configurable import ConfigurationType
from const import Const
from global_controller import global_controller_genesis2
from from_magma import FromMagma


class MyGlobalController(generator.Generator):
    def __init__(self, addr_width, data_width):
        super().__init__()
        super().__init__()

        self.addr_width = addr_width
        self.data_width = data_width
        self.config_type = ConfigurationType(self.addr_width, self.data_width)

        self.add_ports(
            jtag_in=magma.In(JTAGType),
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
        }
        generator = wrapper.generator(mode="declare", type_map=type_map)
        self.underlying = FromMagma(generator())

        self.wire(self.jtag_in.tdi, self.underlying.tdi)
        # TODO(rsetaluri): Fix 'tdo'.
        #self.wire(self.jtag_in.tdo, self.underlying.tdo)
        self.wire(self.jtag_in.tms, self.underlying.tms)
        self.wire(self.jtag_in.tck, self.underlying.tck)
        self.wire(self.jtag_in.trst_n, self.underlying.trst_n)
        self.wire(self.clk_in, self.underlying.clk_in)
        self.wire(self.reset_in, self.underlying.reset_in)

        self.wire(self.underlying.config_addr_out, self.config.config_addr)
        self.wire(self.underlying.config_data_out, self.config.config_data)
        self.wire(self.underlying.clk_out, self.clk_out)
        self.wire(self.underlying.reset_out, self.reset_out)

        # TODO(rsetaluri): wire debug read_data into underlying.config_data_in.
        self.wire(Const(magma.bits(0, self.data_width)),
                  self.underlying.config_data_in)

    def name(self):
        return f"GlobalController_{self.addr_width}_{self.data_width}"
