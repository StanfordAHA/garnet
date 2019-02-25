import generator
import magma
from const import Const


class Foo(gemstone.generator.Generator):
    def __init__(self):
        super().__init__()

        self.add_ports(
            O=magma.Out(magma.Bits(16)),
        )

        self.wire(Const(magma.bits(0, 16)), self.O)

    def name(self):
        return "Foo"


if __name__ == "__main__":
    foo_gen = Foo()
    circ = foo_gen.circuit()
    print (circ)
    magma.compile("foo", circ, output="coreir")
    print(open("foo.json").read())
