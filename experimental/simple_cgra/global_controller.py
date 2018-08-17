import generator
import magma
from jtag_type import JTAGType
from configurable import ConfigurationType


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

    def name(self):
        return f"GlobalController_{self.addr_width}_{self.data_width}"
