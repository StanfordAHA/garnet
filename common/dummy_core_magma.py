import magma
from common.core import Core
from generator.configurable import ConfigurationType
from common.mux_with_default import MuxWithDefaultWrapper


class DummyCore(Core):
    def __init__(self):
        super().__init__()
        self.add_ports(
            data_in_16b=magma.In(magma.Bits(16)),
            data_out_16b=magma.Out(magma.Bits(16)),
            data_in_1b=magma.In(magma.Bits(1)),
            data_out_1b=magma.Out(magma.Bits(1)),
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            config=magma.In(ConfigurationType(8, 32)),
            read_config_data=magma.Out(magma.Bits(32))
        )

        # Dummy core just passes inputs through to outputs
        self.wire(self.ports.data_in_16b, self.ports.data_out_16b)
        self.wire(self.ports.data_in_1b, self.ports.data_out_1b)

        # Add some config registers
        self.add_configs(
            dummy_1=32,
            dummy_2=32
        )

        # Create mux allow for reading of config regs
        num_mux_inputs = len(self.registers.values())
        self.read_data_mux = MuxWithDefaultWrapper(num_mux_inputs, 32, 8, 0)
        # Connect config_addr to mux select
        self.wire(self.read_data_mux.ports.S, self.ports.config.config_addr)
        # Connect config_read to mux enable
        self.wire(self.read_data_mux.ports.EN[0], self.ports.config.read[0])
        self.wire(self.read_data_mux.ports.O, self.ports.read_config_data)
        for i, reg in enumerate(self.registers.values()):
            reg.set_addr(i)
            reg.set_addr_width(8)
            reg.set_data_width(32)
            # wire output to read_data_mux inputs
            self.wire(reg.ports.O, self.read_data_mux.ports.I[i])
            # Wire config addr and data to each register
            self.wire(self.ports.config.config_addr, reg.ports.config_addr)
            self.wire(self.ports.config.config_data, reg.ports.config_data)
            # Wire config write to each reg's write port
            self.wire(self.ports.config.write[0], reg.ports.config_en)
            self.wire(self.ports.reset, reg.ports.reset)

    def inputs(self):
        return [self.ports.data_in_1b, self.ports.data_in_16b]

    def outputs(self):
        return [self.ports.data_out_1b, self.ports.data_out_16b]

    def name(self):
        return "DummyCore"
