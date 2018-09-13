import magma
from common.mux_wrapper import MuxWrapper
from generator.configurable import Configurable, ConfigurationType


class CB(Configurable):
    def __init__(self, height, width):
        super().__init__()

        self.height = height
        self.width = width
        sel_bits = magma.bitutils.clog2(self.height)

        self.mux = MuxWrapper(self.height, self.width)

        T = magma.Bits(self.width)

        self.add_ports(
            I=magma.In(magma.Array(self.height, T)),
            O=magma.Out(T),
            clk=magma.In(magma.Clock),
            config=magma.In(ConfigurationType(8, 32)),
            read_config_data=magma.Out(32)
        )
        self.add_configs(
           S=sel_bits,
        )

        # read_config_data output
        num_config_reg = len(self.registers)
        if(num_config_reg > 1):
            self.read_config_data_mux = MuxWrapper(num_config_reg, 32)
            self.wire(self.read_config_data_mux.ports.O,
                      self.ports.read_config_data)
            for idx, reg in enumerate(self.registers.values()):
                self.wire(reg.ports.O, self.read_config_data_mux.ports.I[idx])
        # If we only have 1 config register, we don't need a mux
        # Wire sole config register directly to read_config_data_output
        else:
            self.wire(self.registers[0].ports.O, self.ports.read_config_data)

        self.wire(self.ports.I, self.mux.ports.I)
        self.wire(self.registers.S.ports.O, self.mux.ports.S)
        self.wire(self.mux.ports.O, self.ports.O)

        for idx, reg in enumerate(self.registers.values()):
            reg.set_addr(idx)
            reg.set_addr_width(8)
            reg.set_data_width(32)
            self.wire(self.ports.config.config_addr, reg.ports.config_addr)
            self.wire(self.ports.config.config_data, reg.ports.config_data)

    def name(self):
        return f"CB_{self.height}_{self.width}"
