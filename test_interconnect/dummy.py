from common.core import Core
import magma


class DummyCore(Core):
    def __init__(self):
        super().__init__()

        # PEP 8 rename
        t_data = magma.Bits(16)

        self.add_ports(
            data_in=magma.In(t_data),
            data_out=magma.Out(t_data),
        )

        self.wire(self.ports.data_in, self.ports.data_out)

    def inputs(self):
        return [self.ports.data_in]

    def outputs(self):
        return [self.ports.data_out]

    def name(self):
        return "DummyCore"
