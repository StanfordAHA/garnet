from itertools import product
import magma as m
import util
from generator import Generator
from interconnect import Interconnect
from global_controller import GlobalController
from mem_core import MemCore
from pe_core import PECore
from tile import Tile


class CGRA(Generator):
    def __init__(self, m_=16, n_=16):
        super().__init__()
        self.__interconnect = Interconnect(m_, n_)
        for i, j in self.__interconnect.indices():
            core = PECore()
            self.__interconnect.set_tile(i, j, Tile(core))
        self.__global_controller = GlobalController()

    @property
    @util.subgenerator
    def interconnect(self):
        return self.__interconnect

    @property
    @util.subgenerator
    def global_controller(self):
        return self.__global_controller

    def _generate_impl(self):
        ic_circuit = self.__interconnect.generate()
        gc_circuit = self.__global_controller.generate()

        interface = ic_circuit.interface.decl()
        for name, type_ in self.__global_controller.jtag_inputs.items():
            interface += [name, type_]

        class _CGRA(m.Circuit):
            name = "CGRA"
            IO = interface

            @classmethod
            def definition(io):
                ic_inst = ic_circuit()
                gc_inst = gc_circuit()
                util.wrap(ic_inst, io)
                for name in self.__global_controller.jtag_inputs:
                    m.wire(getattr(io, name), getattr(gc_inst, name))
                    m.wire(m.bits(0, self.__global_controller.data_width),
                           gc_inst.config_data_in)

        return _CGRA


def main():
    cgra = CGRA(4, 4)
    cgra_circuit = cgra.generate()
    prefix = "experimental/simple_cgra/cgra"
    m.compile(prefix, cgra_circuit, output="coreir")
    print(open(f"{prefix}.json").read())


if __name__ == "__main__":
    main()
