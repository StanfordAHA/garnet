import magma as m
from gemstone.common.core import ConfigurableCore, PnRTag, ConfigurationType, Core
from kratos import Generator, posedge, always_ff, mux
from kratos.util import to_magma


class KratosValidIOCore(Generator):
    __cache = {}

    def __init__(self, count_width):
        super().__init__("ValidIO")
        # the upper count as an IO from output config
        self.max_cycle = self.input("max_cycle", count_width)
        # start signal
        self.start = self.input("start", 1)
        # clks and reset
        # CGRA uses posedge reset
        self.clk = self.clock("clk")
        self.rst = self.reset("reset")
        self.stall = self.input("stall", 1)
        self.start_state = self.enum("start_state", {"io_valid_idle": 0,
                                                     "io_valid_count": 1})
        self.has_start = self.var("has_start", self.start_state)
        self.count = self.var("count", count_width)
        # valid output
        self.valid = self.var("valid", 1)
        # only if the state is in counting and count is larger or equal to max_cycle
        self.wire(self.valid,
                  (self.has_start == self.start_state.io_valid_count) & (self.count < self.max_cycle))
        # normal output
        self.f2io_1 = self.input("f2io_1", 1)
        # mode
        self.mode = self.input("mode", 1)
        # output
        self.out = self.output("out", 1)
        self.wire(self.out, mux(self.mode == 1, self.valid, self.f2io_1))

        # counter enable logic
        self.cen = self.var("cen", 1)
        self.wire(self.cen,
                  (self.has_start == self.start_state.io_valid_count) & (self.count < self.max_cycle) & (~self.stall))

        # add code blocks
        self.add_always(self.start_signal)
        self.add_always(self.count_cycle)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def start_signal(self):
        if self.rst:
            self.has_start = self.start_state.io_valid_idle
        elif self.start:
            self.has_start = self.start_state.io_valid_count

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def count_cycle(self):
        if self.rst:
            self.count = 0
        elif self.cen:
            self.count = self.count + 1

    @staticmethod
    def get_core(width):
        if width in KratosValidIOCore.__cache:
            return KratosValidIOCore.__cache[width]
        else:
            core = KratosValidIOCore(width)
            circ = to_magma(core)
            KratosValidIOCore.__cache[width] = circ
            return circ


class IOCoreBase(Core):
    def __init__(self):
        super().__init__()

    def _add_ports(self):
        ports = m.IO(
            glb2io_16=m.In(m.Bits[16]),
            glb2io_1=m.In(m.Bits[1]),
            io2glb_16=m.Out(m.Bits[16]),
            io2glb_1=m.Out(m.Bits[1]),
            f2io_16=m.In(m.Bits[16]),
            f2io_1=m.In(m.Bits[1]),
            io2f_16=m.Out(m.Bits[16]),
            io2f_1=m.Out(m.Bits[1])
        )
        try:
            self.io += ports
        except AttributeError:
            self.io = ports
        

    def inputs(self):
        return [self.io.glb2io_16, self.io.glb2io_1,
                self.io.f2io_16, self.io.f2io_1]

    def outputs(self):
        return [self.io.io2glb_16, self.io.io2glb_1,
                self.io.io2f_16, self.io.io2f_1]

    def name(self):
        return "io_core"

    def pnr_info(self):
        return [PnRTag("I", 2, self.DEFAULT_PRIORITY),
                PnRTag("i", 1, self.DEFAULT_PRIORITY)]


class IOCore(IOCoreBase):
    def __init__(self):
        super().__init__()
        self._add_ports()

        m.wire(self.io.glb2io_16, self.io.io2f_16)
        m.wire(self.io.glb2io_1, self.io.io2f_1)
        m.wire(self.io.f2io_16, self.io.io2glb_16)
        m.wire(self.io.f2io_1, self.io.io2glb_1)


class IOCoreValid(ConfigurableCore, IOCoreBase):
    def __init__(self, config_addr_width=8, config_data_width=32):
        super().__init__(config_addr_width, config_data_width)
        self._add_ports()

        max_cycle_width = 22

        self.io += m.IO(
            stall=m.In(m.Bits[1])
        )

        self.io += m.IO(config=m.In(ConfigurationType(self.config_addr_width, self.config_data_width)))

        m.wire(self.io.glb2io_16, self.io.io2f_16)
        m.wire(self.io.glb2io_1, self.io.io2f_1)
        m.wire(self.io.f2io_16, self.io.io2glb_16)

        self.core = KratosValidIOCore.get_core(22)
        for p in {"clk", "reset", "stall"}:
            m.wire(self.io[p], self.core.ports[p])
        self.add_config("max_cycle", max_cycle_width)
        self.add_config("mode", 1)

        m.wire(self.registers["max_cycle"].O, self.core.max_cycle)
        m.wire(self.registers["mode"].O, self.core.mode)
        m.wire(self.io.f2io_1, self.core.f2io_1)
        m.wire(self.io.io2glb_1, self.core.out)
        m.wire(self.io.glb2io_1, self.core.start)

        self._setup_config()

    def get_config_bitstream(self, instr):
        return []  # pragma: nocover

    def instruction_type(self):
        raise NotImplementedError()  # pragma: nocover


if __name__ == "__main__":
    core = IOCoreValid(8, 32)
    m.compile("io", core, inline=False)
