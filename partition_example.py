import magma
import mantle
from gemstone.generator.generator import Generator
from gemstone.generator.from_magma import FromMagma
from gemstone.common.mux_wrapper import MuxWrapper
from gemstone.common.ungroup import ungroup
from gemstone.common.group import group


class SomeFunctionalCell(Generator):
    def __init__(self, width):
        super().__init__()

        self.width = width
        T = magma.Bits[self.width]

        self.add_ports(
            I=magma.In(T),
            O=magma.Out(T),
        )
        assert(self.width > 1)
        not_ = FromMagma(mantle.DefineNegate(self.width-1))
        #not_2 = FromMagma(mantle.DefineNegate(1))
        self.wire(self.ports.I[0:(self.width-1)], not_.ports.I[0:(self.width-1)])
        self.wire(self.ports.O[0:(self.width-1)], not_.ports.O[0:(self.width-1)])
        self.wire(self.ports.I[self.width-1], self.ports.O[self.width-1])
        #self.wire(self.ports.I[self.width-1], not_2.ports.I[0])
        #self.wire(self.ports.O[self.width-1], not_2.ports.O[0])
        #self.wire(self.ports.I, self.ports.O)

    def name(self):
        return f"Cell{self.width}"


class ChainOfCells(Generator):
    def __init__(self):
        super().__init__()

        self.width = 2
        self.length = 8

        T = magma.Bits[self.width]

        self.add_ports(
            I=magma.In(T),
            O=magma.Out(T),
        )

        self.cells = [SomeFunctionalCell(self.width) for _ in range(self.length)]

        self.wire(self.ports.I, self.cells[0].ports.I)
        for i, cell in enumerate(self.cells):
            if i == (len(self.cells) - 1):
                self.wire(cell.ports.O, self.ports.O)
                continue
            self.wire(cell.ports.O, self.cells[i + 1].ports.I)

    def name(self):
        return "ChainOfCells"


gen = ChainOfCells()
#print(f"DIRECTION: {dir(gen.ports.I[0].type())}")
#print(f"DIRECTION: {gen.ports.I.base_type()}")
#port = gen.ports.I[0]
#print(f"OPS: {port._ops[0].index}")
#print(f"DIRECTION: {dir(port.base_type())}")
#print(f"DIRECTION: {port.base_type().value}")
ungroup(gen)
#group(gen, *gen.cells[0:2])
circ = gen.circuit()
print (repr(circ))
magma.compile(circ.name, circ, output="coreir-verilog")

#inst = circ.instances[0]
#print (inst.name)
#print (type(inst).name)
#print (type(inst)().name)

#print ([inst.name for inst in circ.instances])
#print (ChainOfCells().name())
#print (repr(ChainOfCells().circuit()))
