import magma
from generator.configurable import Configurable, ConfigurationType
from common.core import Core
from generator.const import Const
from generator.from_magma import FromMagma
from generator.from_verilog import FromVerilog
from memory_core import memory_core_genesis2


class MemCore(Core):
    def __init__(self, data_width, data_depth):
        super().__init__()

        self.data_width = data_width
        self.data_depth = data_depth
        TData = magma.Bits(self.data_width)

        self.add_ports(
            data_in=magma.In(TData),
            addr_in=magma.In(TData),
            data_out=magma.Out(TData),
            clk=magma.In(magma.Clock),
            config=magma.In(ConfigurationType(8, 32)),
        )

        wrapper = memory_core_genesis2.memory_core_wrapper
        param_mapping = memory_core_genesis2.param_mapping
        type_map = {
            "clk_in": magma.In(magma.Clock),
        }
        generator = wrapper.generator(
            param_mapping, mode="declare", type_map=type_map)
        circ = generator(data_width=self.data_width, data_depth=self.data_depth)
        self.underlying = FromMagma(circ)

        self.wire(self.data_in, self.underlying.data_in)
        self.wire(self.addr_in, self.underlying.addr_in)
        self.wire(self.data_out, self.underlying.data_out)
        self.wire(self.config.config_addr, self.underlying.config_addr[24:32])
        self.wire(self.config.config_data, self.underlying.config_data)

        # TODO(rsetaluri): Actually wire these inputs.
        signals = (
            ("clk_en", 1),
            ("reset", 1),
            ("config_en", 1),
            ("config_en_sram", 4),
            ("config_en_linebuf", 1),
            ("wen_in", 1),
            ("ren_in", 1),
            ("chain_wen_in", 1),
            ("config_read", 1),
            ("config_write", 1),
            ("chain_in", self.data_width),
            ("flush", 1),
        )
        for name, width in signals:
            port = getattr(self.underlying, name)
            val = magma.bits(0, width) if width > 1 else magma.bit(0)
            self.wire(Const(val), port)
        self.wire(Const(magma.bits(0, 24)), self.underlying.config_addr[0:24])

    def inputs(self):
        return [self.data_in, self.addr_in]

    def outputs(self):
        return [self.data_out]

    def name(self):
        return "MemCore"
