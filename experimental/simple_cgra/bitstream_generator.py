import generator


class BitstreamGenerator:
    def __init__(self):
        self.configuration = []

    def configure(self, register, value):
        assert isinstance(register, gemstone.generator.Generator._PortReference)
        self.configuration.append((register, value))

    def generate(self):
        for register, value in self.configuration:
            addr = register._owner.addr
            print (addr, value)
