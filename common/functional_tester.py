import fault


class FunctionalTester(fault.Tester):
    def __init__(self, circuit, clock, functional_model, input_mapping=None):
        super().__init__(circuit, clock)
        self.functional_model = functional_model
        self.input_mapping = input_mapping

    def eval(self):
        super().eval()
        inputs = []
        for value, port in zip(self.test_vectors[-2],
                               self.circuit.interface.ports.values()):
            if port.isoutput():
                inputs.append(value)
        if self.input_mapping:
            inputs = self.input_mapping(*inputs)
        self.functional_model(*inputs)
