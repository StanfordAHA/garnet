import generator
import magma


class FooGenerator(gemstone.generator.Generator):
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


class BarGenerator(gemstone.generator.Generator):
    def __init__(self):
        super().__init__()

        self.add_ports(
            I=magma.In(magma.Bit),
            O=magma.Out(magma.Bit),
        )

        self.wire(self.I, self.O)

    def name(self):
        return "Bar"


def introduce_clock(module):
    module.add_ports(clk=magma.In(magma.Clock))
    for child in module.children():
        introduce_clock(child)
    for child in module.children():
        module.wire(module.clk, child.clk)


if __name__ == "__main__":
    foo_generator = FooGenerator()

    # Now we can dynamically add and wire clocks.
    introduce_clock(foo_generator)

    FooCircuit = foo_gemstone.generator.circuit()
    magma.compile("foo", FooCircuit, output="coreir")
    print(open("foo.json").read())
