from typing import List
from abc import ABC, abstractmethod
from gemstone.common.collections import DotDict
from global_buffer.global_buffer_magma import GlobalBuffer
import math
import json


def AXIConfigMap(config_addr_width, config_data_width,
                 core_addr_width, feature_addr_width, reg_addr_width,
                 byte_addressable=True):

    _AXIConfigMap = DotDict()
    _AXIConfigMap.config_addr_width = config_addr_width
    _AXIConfigMap.config_data_width = config_data_width
    _AXIConfigMap.core_addr_width = core_addr_width
    _AXIConfigMap.feature_addr_width = feature_addr_width
    _AXIConfigMap.reg_addr_width = reg_addr_width
    _AXIConfigMap.byte_addressable = byte_addressable

    return _AXIConfigMap


# TODO(kongty): For now, it has nothing to do with RTL generation.
class Glb:
    def __init__(self, global_buffer: GlobalBuffer):
        # TODO(kongty): Hand-written address mapping should migrate to generator
        self.config_map = AXIConfigMap(global_buffer.axi_addr_width,
                                       global_buffer.cfg_data_width,
                                       2, 4, 4, True)
        self.num_io = global_buffer.num_io
        self.num_cfg = global_buffer.num_cfg
        self.num_banks = global_buffer.num_banks

        # TODO(kongty): Hand-written controllers should migrate to generator
        self.io_ctrl = IOController(self, 1, self.num_io)
        self.cfg_ctrl = ParCfgController(self, 2, self.num_cfg)
        self.cores: List["GlbCore"] = [self.io_ctrl, self.cfg_ctrl]

    def dump_all_config(self):
        result = []
        for core in self.cores:
            for feature in core.features:
                for reg in feature.registers.values():
                    result.append(reg)
        return result

    def config(self, collateral):
        num_total_bank = sum([pair[1] for pair in collateral])
        if num_total_bank > self.num_banks:
            raise ValueError(f"Cannot use more than {self.num_banks}"
                             f"in the global buffer")
        collateral_sorted = sorted(collateral, key=lambda tup: tup[1])
        num_app_io = len(collateral_sorted)
        for (idx, (io, num_bank)) in enumerate(collateral_sorted):
            io_ctrl_idx = int((self.num_io / num_app_io) * idx)
            # TODO(kongty): Need to move to lassen framework in the future
            _mode = self.io_ctrl.features[io_ctrl_idx].registers['mode']
            _switch_sel = self.io_ctrl.features[io_ctrl_idx]\
                    .registers['switch_sel']
            if io == 'in':
                _mode['value'] = 1
                _switch_sel['value'] = _switch_sel['range'] - 1
            elif io == 'out':
                _mode['value'] = 2
                _switch_sel['value'] = _switch_sel['range'] - 1
            elif io == 'sram':
                _mode['value'] = 3
                _switch_sel['value'] = _switch_sel['range'] - 1
            else:
                _mode['value'] = 0

        return self.get_bitstream()

    def get_bitstream(self):
        result = []
        for core in self.cores:
            for feature in core.features:
                for reg in feature.registers.values():
                    # If register value is default value, do not need to config
                    if reg['default'] == reg['value']:
                        continue
                    result.append((reg['addr'], reg['value']))
        return result


class GlbCore(ABC):
    def __init__(self, glb: "Glb", core_id: int):
        self.glb = glb
        self.core_id = core_id
        self.features: List["GlbFeature"] = []
        self.num_features = 0
        self.feature_addr_width = self.glb.config_map.feature_addr_width
        self.reg_addr_width = self.glb.config_map.reg_addr_width

    def add_feature(self, _feature: "GlbFeature"):
        if self.num_features >= 2**self.feature_addr_width:
            raise ValueError(f"Cannot add more than {self.num_features}"
                             f"features to the core")
        self.features.append(_feature)
        self.num_features = len(self.features)

    @abstractmethod
    def name(self):
        pass


class GlbFeature(ABC):
    def __init__(self, core: "GlbCore", feature_id: int):
        self.glb = core.glb
        self.core = core
        self.feature_id = feature_id
        self.reg_addr_width = self.glb.config_map.reg_addr_width
        self.feature_addr_width = self.glb.config_map.feature_addr_width
        self.core_addr_width = self.glb.config_map.core_addr_width
        self.config_data_width = self.glb.config_map.config_data_width
        self.byte_addressable = self.glb.config_map.byte_addressable
        if self.byte_addressable:
            self.byte_offset =\
                    int(math.ceil(math.log2(self.config_data_width/8)))
        else:
            self.byte_offset = 0
        self.registers = DotDict()
        self.num_registers = 0

    def add_config(self, name, width, default_value=0):
        if name in self.registers:
            raise ValueError(f"{name} is already a register")
        if self.num_registers >= 2**self.reg_addr_width:
            raise ValueError(f"Cannot add more than {self.num_registers}"
                             f"configuration registers to the feature")

        reg_name = f"{self.name()}_{name}"
        addr = (self.core.core_id << (self.feature_addr_width +
                                      self.reg_addr_width +
                                      self.byte_offset)) | \
               (self.feature_id << (self.reg_addr_width +
                                    self.byte_offset)) | \
               (self.num_registers << self.byte_offset)
        self.registers[f"{name}"] = {"name": reg_name,
                                     "addr": addr,
                                     "range": 2**width,
                                     "default": default_value,
                                     "value": default_value}
        self.num_registers = len(self.registers)

    @abstractmethod
    def name(self):
        pass


class IOController(GlbCore):
    def __init__(self,
                 glb: "Glb",
                 core_id: int,
                 num_io: int):
        super().__init__(glb, core_id)
        self.num_io = num_io

        for i in range(self.num_io):
            _io_address_generator = IOAddrGen(self, i)
            self.add_feature(_io_address_generator)

    def name(self):
        return f"GLB_IOController"


class IOAddrGen(GlbFeature):
    def __init__(self,
                 core: "GlbCore",
                 feature_id: int):
        super().__init__(core, feature_id)

        # reg_addr is determined by the order you add config here
        switch_size = int(math.ceil(self.glb.num_banks / self.core.num_io))
        self.add_config("mode", 2)
        self.add_config("start_addr", 32)
        self.add_config("num_words", 32)
        self.add_config("switch_sel", 4)
        self.add_config("done_delay", switch_size)
        self.add_config("done_gate", 1)
        self.add_config("num_active", 32)
        self.add_config("num_inactive", 32)

    def name(self):
        return f"{self.core.name()}_IOAddrGen_{self.feature_id}"


class ParCfgController(GlbCore):
    def __init__(self,
                 glb: "Glb",
                 core_id: int,
                 num_cfg: int):
        super().__init__(glb, core_id)
        self.num_cfg = num_cfg

        for i in range(self.num_cfg):
            _par_cfg_address_generator = ParCfgAddrGen(self, i)
            self.add_feature(_par_cfg_address_generator)

    def name(self):
        return f"GLB_ParCfgController"


class ParCfgAddrGen(GlbFeature):
    def __init__(self,
                 core: "GlbCore",
                 feature_id: int):
        super().__init__(core, feature_id)

        # reg_addr is determined by the order you add config here
        switch_size = int(math.ceil(self.glb.num_banks / self.core.num_cfg))
        self.add_config("start_addr", 32)
        self.add_config("num_words", 32)
        self.add_config("switch_sel", switch_size)

    def name(self):
        return f"{self.core.name()}_ParCfgAddrGen_{self.feature_id}"
