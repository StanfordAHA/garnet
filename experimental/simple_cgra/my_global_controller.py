import generator
import magma
from jtag_type import JTAGType
from configurable import ConfigurationType
from const import Const


class GlobalController(generator.Generator):
    def __init__(self, addr_width, data_width):
        super().__init__()
        super().__init__()

        self.addr_width = addr_width
        self.data_width = data_width
        self.config_type = ConfigurationType(self.addr_width, self.data_width)

        self.add_ports(
            jtag_in=magma.In(JTAGType),
            config=magma.Out(self.config_type),
        )

        # TODO(rsetaluri): Actual impl.
        self.wire(Const(magma.bits(0, self.addr_width)),
                  self.config.config_addr)
        self.wire(Const(magma.bits(0, self.data_width)),
                  self.config.config_data)


    def name(self):
        return f"GlobalController_{self.addr_width}_{self.data_width}"
