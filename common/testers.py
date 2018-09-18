from fault.functional_tester import FunctionalTester


class ResetTester(FunctionalTester):
    def __init__(self, circuit, clock, functional_model, input_mapping=None,
                 reset_port=None):
        super().__init__(circuit, clock, functional_model, input_mapping)
        if reset_port is None:
            reset_port = circuit.reset
        self.reset_port = reset_port

    def reset(self):
        self.functional_model.reset()
        self.expect_any_outputs()
        self.poke(self.reset_port, 1)
        self.eval()
        self.poke(self.reset_port, 0)


class ConfigurationTester(FunctionalTester):
    def configure(self, addr, data):
        self.functional_model.configure(addr, data)
        self.poke(self.clock, 0)
        self.poke(self.reset_port, 0)
        self.poke(self.circuit.config_addr, addr)
        self.poke(self.circuit.config_data, data)
        self.poke(self.circuit.config_en, 1)
        self.step()
