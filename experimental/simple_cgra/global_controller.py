import generator
import magma
from jtag_type import JTAGType


class GlobalController(generator.Generator):
    def __init__(self, addr_width, data_width):
        super().__init__()
        super().__init__()

        self.addr_width = addr_width
        self.data_width = data_width

        self.add_ports(
            jtag_in=magma.In(JTAGType),
        )

    def name(self):
        return "GlobalController"
