from fault.functional_tester import FunctionalTester


class ResetTester(FunctionalTester):
    def reset(self):
        self.functional_model.reset()
        self.poke(self.circuit.reset, 1)
        self.eval()
        self.poke(self.circuit.reset, 0)


class ConfigurationTester(FunctionalTester):
    def configure(self, addr, data):
        self.functional_model.configure(addr, data)
        self.poke(self.clock, 0)
        self.poke(self.circuit.reset, 0)
        self.poke(self.circuit.config_addr, addr)
        self.poke(self.circuit.config_data, data)
        self.poke(self.circuit.config_en, 1)
        self.step()
