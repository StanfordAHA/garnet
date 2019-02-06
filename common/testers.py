from fault.functional_tester import FunctionalTester
from fault.tester import Tester


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
        self.poke(self._circuit.config_addr, addr)
        self.poke(self._circuit.config_data, data)
        self.poke(self._circuit.config_en, 1)
        self.step()


# Use this for tests without functional models
class BasicTester(Tester):
    def __init__(self, circuit, clock, reset_port=None):
        super().__init__(circuit, clock)
        self.reset_port = reset_port

    def configure(self, addr, data, assert_wr=True):
        self.poke(self.clock, 0)
        self.poke(self.reset_port, 0)
        self.poke(self._circuit.config.config_addr, addr)
        self.poke(self._circuit.config.config_data, data)
        self.poke(self._circuit.config.read, 0)
        # We can use assert_wr switch to check that no reconfiguration
        # occurs when write = 0
        if(assert_wr):
            self.poke(self._circuit.config.write, 1)
        else:
            self.poke(self._circuit.config.write, 0)
        #
        self.step(2)
        self.poke(self._circuit.config.write, 0)

    def config_read(self, addr):
        self.poke(self.clock, 0)
        self.poke(self.reset_port, 0)
        self.poke(self._circuit.config.config_addr, addr)
        self.poke(self._circuit.config.read, 1)
        self.poke(self._circuit.config.write, 0)
        self.step(2)

    def reset(self):
        self.poke(self.reset_port, 1)
        self.step(2)
        self.eval()
        self.poke(self.reset_port, 0)
