import generator
import magma


JTAG = magma.Tuple(
    tdi=magma.Bit,
    tdo=magma.Bit,
    tms=magma.Bit,
    tck=magma.Bit,
    trst_n=magma.Bit)


class GlobalController(generator.Generator):
    def __init__(self, addr_width, data_width):
        super().__init__()
        super().__init__()

        self.addr_width = addr_width
        self.data_width = data_width

        self.add_ports(
            jtag_in=magma.In(JTAG),
        )

    def name(self):
        return "GlobalController"
