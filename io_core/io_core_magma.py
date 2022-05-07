import magma
from gemstone.common.core import ConfigurableCore, PnRTag, ConfigurationType, Core
from gemstone.generator import FromMagma
from kratos import Generator, posedge, always_ff, mux, ternary
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
        self.add_ports(
            glb2io_16=magma.In(magma.Bits[16]),
            glb2io_1=magma.In(magma.Bits[1]),
            io2glb_16=magma.Out(magma.Bits[16]),
            io2glb_1=magma.Out(magma.Bits[1]),
            f2io_16=magma.In(magma.Bits[16]),
            f2io_1=magma.In(magma.Bits[1]),
            io2f_16=magma.Out(magma.Bits[16]),
            io2f_1=magma.Out(magma.Bits[1])
        )

    def inputs(self):
        return [self.ports.glb2io_16, self.ports.glb2io_1,
                self.ports.f2io_16, self.ports.f2io_1]

    def outputs(self):
        return [self.ports.io2glb_16, self.ports.io2glb_1,
                self.ports.io2f_16, self.ports.io2f_1]

    def name(self):
        return "io_core"

    def pnr_info(self):
        return [PnRTag("I", 2, self.DEFAULT_PRIORITY),
                PnRTag("i", 1, self.DEFAULT_PRIORITY)]


class IOCore(IOCoreBase):
    def __init__(self):
        super().__init__()
        self._add_ports()

        self.wire(self.ports.glb2io_16, self.ports.io2f_16)
        self.wire(self.ports.glb2io_1, self.ports.io2f_1)
        self.wire(self.ports.f2io_16, self.ports.io2glb_16)
        self.wire(self.ports.f2io_1, self.ports.io2glb_1)


class IOCoreValid(ConfigurableCore, IOCoreBase):
    def __init__(self, config_addr_width=8, config_data_width=32):
        super().__init__(config_addr_width, config_data_width)
        self._add_ports()

        max_cycle_width = 22

        self.add_ports(
            stall=magma.In(magma.Bits[1])
        )

        self.add_port("config", magma.In(ConfigurationType(self.config_addr_width, self.config_data_width)))

        self.wire(self.ports.glb2io_16, self.ports.io2f_16)
        self.wire(self.ports.glb2io_1, self.ports.io2f_1)
        self.wire(self.ports.f2io_16, self.ports.io2glb_16)

        self.core = FromMagma(KratosValidIOCore.get_core(22))
        for p in {"clk", "reset", "stall"}:
            self.wire(self.ports[p], self.core.ports[p])
        self.add_config("max_cycle", max_cycle_width)
        self.add_config("mode", 1)

        self.wire(self.registers["max_cycle"].ports.O, self.core.ports.max_cycle)
        self.wire(self.registers["mode"].ports.O, self.core.ports.mode)
        self.wire(self.ports.f2io_1, self.core.ports.f2io_1)
        self.wire(self.ports.io2glb_1, self.core.ports.out)
        self.wire(self.ports.glb2io_1, self.core.ports.start)

    def get_config_bitstream(self, instr):
        return []  # pragma: nocover

    def instruction_type(self):
        raise NotImplementedError()  # pragma: nocover


class KratosIOCoreDelay(Generator):
    core = None

    def __init__(self):
        super(KratosIOCoreDelay, self).__init__("KratosIOCoreDelay")
        glb_ports = []
        for width in [1, 16]:
            glb_name = f"glb2io_{width}"
            glb_ports.append(self.input(glb_name, width))
            self.input(f"f2io_{width}", width)
        for width in [1, 16]:
            glb_ports.append(self.output(f"io2glb_{width}", width))
            self.output(f"io2f_{width}", width)

        clk = self.clock("clk")

        @always_ff((posedge, clk))
        def delay_logic(en_name, reg_name):
            if self.ports[en_name]:
                self.vars[reg_name] = self.ports[port_name]

        for port in glb_ports:
            port_name = port.name
            reg = self.var(port_name + "_reg", port.width)
            delay = self.input(port_name + "_delay_en", 1)
            self.add_always(delay_logic, en_name=delay.name, reg_name=reg.name)

        # dealing with pass though logic or muxing logic
        for width in [1, 16]:
            glb_port = f"glb2io_{width}"
            self.wire(self.ports[f"io2f_{width}"],
                      ternary(self.ports[f"glb2io_{width}_delay_en"], self.vars[f"glb2io_{width}_reg"],
                              self.ports[glb_port]))
            glb_port = f"f2io_{width}"
            self.wire(self.ports[f"io2glb_{width}"],
                      ternary(self.ports[f"io2glb_{width}_delay_en"], self.vars[f"io2glb_{width}_reg"],
                              self.ports[glb_port]))

    @staticmethod
    def get_core():
        if KratosIOCoreDelay.core is None:
            c = KratosIOCoreDelay()
            circ = to_magma(c)
            KratosIOCoreDelay.core = circ
        return KratosIOCoreDelay.core


class IOCoreDelay(ConfigurableCore, IOCoreBase):
    def __init__(self, config_addr_width=8, config_data_width=32):
        super().__init__(config_addr_width, config_data_width)
        self._add_ports()
        self.add_port("config", magma.In(ConfigurationType(self.config_addr_width, self.config_data_width)))

        self.core = FromMagma(KratosIOCoreDelay.get_core())
        # wiring up the ports
        self.wire(self.ports.clk, self.core.ports.clk)
        for width in [1, 16]:
            for prefix in ["glb2io", "io2f", "f2io", "io2glb"]:
                port_name = f"{prefix}_{width}"
                self.wire(self.ports[port_name], self.core.ports[port_name])
            # add config
            for prefix in ["glb2io", "io2glb"]:
                reg_name = f"{prefix}_{width}_delay_en"
                self.add_config(reg_name, 1)
                self.wire(self.registers[reg_name].ports.O, self.core.ports[reg_name])

    def get_config_bitstream(self, instr):
        return []  # pragma: nocover

    def instruction_type(self):
        raise NotImplementedError()  # pragma: nocover


if __name__ == "__main__":
    core = IOCoreValid(8, 32)
    magma.compile("io", core.circuit(), inline=False)
