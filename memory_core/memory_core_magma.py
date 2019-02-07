import magma
import mantle
from generator.configurable import ConfigurationType
from common.core import Core, CoreFeature
from common.coreir_wrap import CoreirWrap
from generator.const import Const
from generator.from_magma import FromMagma
from generator.from_verilog import FromVerilog
from memory_core import memory_core_genesis2
from typing import List


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
        # we have five features in total
        # 0:   LINEBUF
        # 1-4: SMEM
        # current setup is already in line buffer mode, so we pass self in
        # notice that config_en_linebuf is to change the address in the
        # line buffer mode, which is not used in practice
        self.__features: List[CoreFeature] = [CoreFeature(self, 0)]
        for sram_index in range(4):
            core_feature = CoreFeature(self, sram_index + 1)
            self.__features.append(core_feature)

        for idx, core_feature in enumerate(self.__features):
            self.add_port(f"config_{idx}", magma.In(ConfigurationType(8, 32)))
            # port aliasing
            core_feature.ports["config"] = self.ports[f"config_{idx}"]
        # or the signal up
        t = ConfigurationType(8, 32)
        t_names = ["config_addr", "config_data", "read", "write"]
        or_gates = {}
        for t_name in t_names:
            port_type = t[t_name]
            or_gate = FromMagma(mantle.DefineOr(len(self.__features),
                                                len(port_type)))
            for idx, core_feature in enumerate(self.__features):
                self.wire(or_gate.ports[f"I{idx}"],
                          core_feature.ports.config[t_name])
            or_gates[t_name] = or_gate
        self.wire(or_gates["config_addr"].ports.O,
                  self.underlying.ports.config_addr[24:32])
        self.wire(or_gates["config_data"].ports.O,
                  self.underlying.ports.config_data)
        self.wire(or_gates["write"].ports.O[0],
                  self.underlying.ports.config_en)

        # read data out
        for idx, core_feature in enumerate(self.__features):
            self.add_port(f"read_config_data_{idx}",
                          magma.Out(magma.Bits(32)))
            # port aliasing
            core_feature.ports["read_config_data"] = \
                self.ports[f"read_config_data_{idx}"]
        # MEM config
        self.wire(self.ports.read_config_data_0,
                  self.underlying.ports.read_data)
        # SRAM
        for sram_index in range(4):
            core_feature = self.__features[sram_index + 1]
            self.wire(core_feature.ports.read_config_data,
                      self.underlying.ports[f"read_data_sram_{sram_index}"])
            # also need to wire the sram signal
            # we or the read or write signal up
            or_gate = FromMagma(mantle.DefineOr(2, 1))
            self.wire(or_gate.ports.I0, core_feature.ports.config.read)
            self.wire(or_gate.ports.I1, core_feature.ports.config.write)
            self.wire(self.underlying.ports["config_en_sram"][sram_index],
                      or_gate.ports.O[0])

    def inputs(self):
        return [self.ports.data_in, self.ports.addr_in, self.ports.flush,
                self.ports.ren_in, self.ports.wen_in]

    def outputs(self):
        return [self.ports.data_out]

    def features(self):
        return self.__features

    def name(self):
        return "MemCore"
