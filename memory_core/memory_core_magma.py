import magma
import mantle
from generator.configurable import ConfigurationType
from common.core import Core, CoreFeature
from common.coreir_wrap import CoreirWrap
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
        TBit = magma.Bits(1)

        self.add_ports(
            data_in=magma.In(TData),
            addr_in=magma.In(TData),
            data_out=magma.Out(TData),
            clk=magma.In(magma.Clock),
            config=magma.In(ConfigurationType(8, 32)),
            reset=magma.In(magma.AsyncReset),
            flush=magma.In(TBit),
            wen_in=magma.In(TBit),
            ren_in=magma.In(TBit),
            stall=magma.In(magma.Bits(4))
        )

        wrapper = memory_core_genesis2.memory_core_wrapper
        param_mapping = memory_core_genesis2.param_mapping
        generator = wrapper.generator(param_mapping, mode="declare")
        circ = generator(data_width=self.data_width,
                         data_depth=self.data_depth)
        self.underlying = FromMagma(circ)

        self.wire(self.ports.data_in, self.underlying.ports.data_in)
        self.wire(self.ports.addr_in, self.underlying.ports.addr_in)
        self.wire(self.ports.data_out, self.underlying.ports.data_out)

        self.wire(self.ports.reset, self.underlying.ports.reset)
        self.wire(self.ports.flush[0], self.underlying.ports.flush)
        self.wire(self.ports.wen_in[0], self.underlying.ports.wen_in)
        self.wire(self.ports.ren_in[0], self.underlying.ports.ren_in)

        # PE core uses clk_en (essentially active low stall)
        self.stallInverter = FromMagma(mantle.DefineInvert(1))
        self.wire(self.stallInverter.ports.I, self.ports.stall[0:1])
        self.wire(self.stallInverter.ports.O[0], self.underlying.ports.clk_en)

        # TODO(rsetaluri): Actually wire these inputs.
        signals = (
            # ("config_en_sram", 4),
            ("config_en_linebuf", 1),
            ("chain_wen_in", 1),
            ("config_read", 1),
            ("config_write", 1),
            ("chain_in", self.data_width),
        )
        for name, width in signals:
            val = magma.bits(0, width) if width > 1 else magma.bit(0)
            self.wire(Const(val), self.underlying.ports[name])
        self.wire(Const(magma.bits(0, 24)),
                  self.underlying.ports.config_addr[0:24])

        config_addr_width = 8
        config_data_width = 32
        # we have five features in total
        # 0:   LINEBUF
        # 1-4: SMEM
        # current setup is already in line buffer mode, so we pass self in
        # notice that config_en_linebuf is to change the address in the
        # line buffer mode, which is not used in practice
        self.__features = [CoreFeature(self, 0,
                                       config_addr_width,
                                       config_data_width)]
        # for the MEM config
        self.wire(self.__features[0].ports.read_config_data_in,
                  self.underlying.ports.read_data)
        for sram_index in range(4):
            # one hot encoding
            core_feature = CoreFeature(self, sram_index + 1,
                                       config_addr_width,
                                       config_data_width)
            # wire read_config_data to 0 since the core doesn't support to
            # read them
            self.wire(core_feature.ports.read_config_data_in,
                      self.underlying.ports.read_data_sram)
            self.wire(core_feature.ports.config_en,
                      self.underlying.ports.config_en_sram[sram_index])
            self.__features.append(core_feature)

        # these signals will be shared by all the features
        # as a result we need to create a mux or fanout
        # because we will won't select two features at the same time
        # we can or them up to the underlying config_data
        or_gate_config_data = FromMagma(mantle.DefineOr(5, config_data_width))
        or_gate_config_addr = FromMagma(mantle.DefineOr(5, config_addr_width))
        for idx, core_feature in enumerate(self.__features):
            self.wire(core_feature.ports.config_out.config_data,
                              or_gate_config_data.ports[f"I{idx}"])
            self.wire(core_feature.ports.config_out.config_addr,
                              or_gate_config_addr.ports[f"I{idx}"])

        self.wire(or_gate_config_data.ports.O,
                  self.underlying.ports.config_data)
        self.wire(or_gate_config_addr.ports.O,
                  self.underlying.ports.config_addr[24:32])

        or_gate_config_en = FromMagma(mantle.DefineOr(5, 1))
        for idx, core_feature in enumerate(self.__features):
            self.wire(core_feature.ports.config_out.write,
                              or_gate_config_en.ports[f"I{idx}"])
        self.wire(or_gate_config_en.ports.O[0],
                  self.underlying.ports.config_en)

        # need to lift up each config data in the core features
        # otherwise magma will complain that it's not connected, thus
        # fail to compile
        for idx, core_feature in enumerate(self.__features):
            self.wire(self.ports.config, core_feature.ports.config)

    def inputs(self):
        return [self.ports.data_in, self.ports.addr_in, self.ports.flush,
                self.ports.ren_in, self.ports.wen_in]

    def outputs(self):
        return [self.ports.data_out]

    def features(self):
        return self.__features

    def name(self):
        return "MemCore"
