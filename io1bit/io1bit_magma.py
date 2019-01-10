import magma
from generator.configurable import ConfigurationType
from common.core import Core
from generator.from_magma import FromMagma
from io1bit import tristate_genesis2


class IO1bit(Core):
    def __init__(self, io_group, side):
        super().__init__()

        wrapper = tristate_genesis2.tristate_wrapper
        generator = wrapper.generator(mode="declare")
        tristate_circ = generator()
        self.tristate = FromMagma(tristate_circ)

        # TODO: I think we can remove these two parameters
        self.io_group = io_group
        self.side = side
        TBit = magma.Bits(1)

        self.add_ports(
            pad=magma.InOut(TBit),
            p2f=magma.Out(TBit),
            f2p_16=magma.In(TBit),
            f2p_1=magma.In(TBit),
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            config=magma.In(ConfigurationType(8, 32)),
            read_config_data=magma.Out(magma.Bits(32))
        )

        self.wire(self.ports.pad, self.tristate.ports.pad)
        self.wire(self.ports.f2p_16, self.tristate.ports.f2p_16)
        self.wire(self.ports.f2p_1, self.tristate.ports.f2p_1)
        # TODO: Change constant 2 to variables
        self.add_configs(
            S=2,
        )
        # IO do not have more than one 32bit configuration register.
        # TODO: Is magma circuit wire zero extended if the number of bits does
        # not match?
        self.wire(self.registers[0].ports.O, self.ports.read_config_data)

        for idx, reg in enumerate(self.registers.values()):
            reg.set_addr(idx)
            reg.set_addr_width(8)
            reg.set_data_width(32)
            self.wire(self.ports.config.config_addr, reg.ports.config_addr)
            self.wire(self.ports.config.config_data, reg.ports.config_data)
            self.wire(reg.ports.config_en, self.ports.config.write[0])

        self.wire(self.ports.f2p_16, self.tristate.ports.f2p_16)
        self.wire(self.ports.f2p_1, self.tristate.ports.f2p_1)
        self.wire(self.ports.pad, self.tristate.ports.pad)
        self.io_bit = self.registers.S.ports.O[0]
        self.out_bus = self.registers.S.ports.O[1]
        self.wire(self.io_bit, self.tristate.ports.io_bit)
        self.wire(self.out_bus, self.tristate.ports.out_bus)

    def inputs(self):
        return None

    def outputs(self):
        return None

    def name(self):
        return "io1bit"
