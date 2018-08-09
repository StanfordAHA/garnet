import generator
import magma


class FooGenerator(generator.Generator):
    def __init__(self):
        super().__init__()

        self.add_ports(
            I=magma.In(magma.Bit),
            O=magma.Out(magma.Bit),
            I1=magma.In(magma.Bit),
            O1=magma.Out(magma.Bit),
        )

        self.bar = BarGenerator()

        self.wire(self.I, self.O)
        self.wire(self.I1, self.bar.I)
        self.wire(self.bar.O, self.O1)

    def name(self):
        return "Foo"


class BarGenerator(generator.Generator):
    def __init__(self):
        super().__init__()

        self.add_ports(
            I=magma.In(magma.Bit),
            O=magma.Out(magma.Bit),
        )

        self.wire(self.I, self.O)
        
    def name(self):
        return "Bar"


if __name__ == "__main__":
    foo_generator = FooGenerator()
    FooCircuit = foo_generator.circuit()
    magma.compile("foo", FooCircuit, output="coreir")
    print(open("foo.json").read())
