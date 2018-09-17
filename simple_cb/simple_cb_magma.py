import magma
from common.mux_wrapper import MuxWrapper
from common.zext_wrapper import ZextWrapper
from generator.configurable import Configurable, ConfigurationType


class CB(Configurable):
    def __init__(self, num_tracks, width):
        super().__init__()

        self.num_tracks = num_tracks
        self.width = width
        sel_bits = magma.bitutils.clog2(self.num_tracks)

        self.mux = MuxWrapper(self.num_tracks, self.width)

        T = magma.Bits(self.width)

        self.add_ports(
            I=magma.In(magma.Array(self.num_tracks, T)),
            O=magma.Out(T),
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            config=magma.In(ConfigurationType(8, 32)),
            read_config_data=magma.Out(magma.Bits(32)),
        )
        self.add_configs(
           S=sel_bits,
        )
        # read_config_data output
        num_config_reg = len(self.registers)
        if(num_config_reg > 1):
            self.read_config_data_mux = MuxWrapper(num_config_reg, 32)
            self.wire(self.ports.config.config_addr,
                      self.read_config_data_mux.ports.S)
            self.wire(self.read_config_data_mux.ports.O,
                      self.ports.read_config_data)
            for idx, reg in enumerate(self.registers.values()):
                self.wire(reg.ports.O, self.read_config_data_mux.ports.I[idx])
                # Wire up config register resets
                self.wire(reg.ports.reset, self.ports.reset)
        # If we only have 1 config register, we don't need a mux
        # Wire sole config register directly to read_config_data_output
        else:
            reg = list(self.registers.values())[0]
            zext = ZextWrapper(reg.width, 32)
            self.wire(reg.ports.O, zext.ports.I)
            zext_out = zext.ports.O
            self.wire(zext_out, self.ports.read_config_data)

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
        return f"CB_{self.num_tracks}_{self.width}"
