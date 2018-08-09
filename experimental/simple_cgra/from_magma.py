import generator
import magma


class FromMagma(generator.Generator):
    def __init__(self, circuit):
        super().__init__()

        assert isinstance(circuit, magma.circuit.DefineCircuitKind)
        self.underlying = circuit

        for port_name, port in self.underlying.interface.ports.items():
            self.add_port(port_name, type(port).flip())

    def circuit(self):
        return self.underlying

    def name(self):
        return self.underlying.name
