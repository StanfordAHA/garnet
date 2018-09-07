import magma
import generator.generator as generator


class FromMagma(generator.Generator):
    def __init__(self, circuit):
        super().__init__()

        circuit_types = (magma.circuit.DefineCircuitKind,
                         magma.circuit.CircuitKind)
        assert isinstance(circuit, circuit_types)
        self.underlying = circuit

        for port_name, port in self.underlying.IO.ports.items():
            self.add_port(port_name, port.flip())

    def circuit(self):
        return self.underlying

    def name(self):
        return self.underlying.name
