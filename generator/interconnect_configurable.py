from common.mux_wrapper import MuxWrapper
from .configurable import Configurable
from common.zext_wrapper import ZextWrapper
import magma
from abc import abstractmethod


class InterconnectConfigurable(Configurable):
    def __init__(self, config_addr_width: int, config_data_width: int):
        super().__init__()
        self.config_addr_width = config_addr_width
        self.config_data_width = config_data_width

        self.read_config_data_mux: MuxWrapper = None

        # ports for reconfiguration
        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
        )

    def _setup_config(self):
        # sort the registers by it's name. this will be the order of config
        # addr index
        config_names = list(self.registers.keys())
        config_names.sort()
        for idx, config_name in enumerate(config_names):
            reg = self.registers[config_name]
            # set the configuration registers
            reg.set_addr(idx)
            reg.set_addr_width(self.config_addr_width)
            reg.set_data_width(self.config_data_width)

            self.wire(self.ports.config.config_addr, reg.ports.config_addr)
            self.wire(self.ports.config.config_data, reg.ports.config_data)
            self.wire(self.ports.config.write[0], reg.ports.config_en)
            self.wire(self.ports.reset, reg.ports.reset)

        # read_config_data output
        num_config_reg = len(config_names)
        if num_config_reg > 1:
            self.read_config_data_mux = MuxWrapper(num_config_reg,
                                                   self.config_data_width)
            sel_bits = self.read_config_data_mux.sel_bits
            # Wire up config_addr to select input of read_data MUX
            self.wire(self.ports.config.config_addr[:sel_bits],
                      self.read_config_data_mux.ports.S)
            self.wire(self.read_config_data_mux.ports.O,
                      self.ports.read_config_data)

            for idx, config_name in enumerate(config_names):
                reg = self.registers[config_name]
                zext = ZextWrapper(reg.width, self.config_data_width)
                self.wire(reg.ports.O, zext.ports.I)
                zext_out = zext.ports.O
                self.wire(zext_out, self.read_config_data_mux.ports.I[idx])
        elif num_config_reg == 1:
            config_name = config_names[0]
            reg = self.registers[config_name]
            zext = ZextWrapper(reg.width, self.config_data_width)
            self.wire(reg.ports.O, zext.ports.I)
            zext_out = zext.ports.O
            self.wire(zext_out, self.ports.read_config_data)

    @abstractmethod
    def name(self):
        pass
