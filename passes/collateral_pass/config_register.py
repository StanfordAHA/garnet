from canal.circuit import get_mux_sel_name
from canal.interconnect import Interconnect
from peak_core.peak_core import PeakCore
from memory_core.memory_core_magma import MemCore


def get_interconnect_regs(interconnect: Interconnect):
    """function to loop through every interconnect object and dump the
    entire configuration space
    """
    result = []
    for x, y in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        # cb first
        for cb_name, cb in tile.cbs.items():
            # get the index
            index = tile.features().index(cb)
            # reg space is always 0 for CB
            reg_addr = 0
            # need to get range
            # notice that we may already replace the mux with aoi + const
            # so we need to get the height from the actual mux
            mux = cb.mux
            mux_range = mux.height
            config_addr = interconnect.get_config_addr(reg_addr, index,
                                                       x, y)
            result.append({
                "name": cb_name,
                "addr": config_addr,
                "range": mux_range
            })

        for switchbox in tile.sbs.values():
            index = tile.features().index(switchbox)
            # sort the reg names
            reg_names = list(switchbox.registers.keys())
            reg_names.sort()
            for sb, sb_mux in switchbox.sb_muxs.values():
                if sb_mux.height > 1:
                    config_name = get_mux_sel_name(sb)
                    assert config_name in reg_names
                    reg_addr = reg_names.index(config_name)
                    mux_range = sb_mux.height
                    config_addr = interconnect.get_config_addr(reg_addr, index,
                                                               x, y)
                    result.append({
                        "name": str(sb),
                        "addr": config_addr,
                        "range": mux_range
                    })
            for node, reg_mux in switchbox.reg_muxs.values():
                if reg_mux.height > 1:
                    config_name = get_mux_sel_name(node)
                    assert config_name in reg_names
                    reg_addr = reg_names.index(config_name)
                    mux_range = reg_mux.height
                    config_addr = interconnect.get_config_addr(reg_addr, index,
                                                               x, y)
                    result.append({
                        "name": str(node),
                        "addr": config_addr,
                        "range": mux_range
                    })

    return result


def get_core_registers(interconnect: Interconnect):
    result = []
    for x, y in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        core = tile.core
        if core is None:
            continue
        if isinstance(core, PeakCore):
            # extract out PE's configuration
            # notice that peak core is a black box. we have no idea what
            # the registers' semantic meaning
            feat_addr = tile.features().index(core)
            regs = list(core.registers.keys())
            regs.sort()
            for idx, reg_name in enumerate(regs):
                reg_addr = idx
                width = core.reg_width[reg_name]
                addr = interconnect.get_config_addr(reg_addr, feat_addr, x, y)
                result.append({
                    "name": reg_name,
                    "addr": addr,
                    "range": 1 << width
                })
        elif isinstance(core, MemCore):
            # memory has five features
            base_feat_addr = tile.features().index(core)
            regs = list(core.registers.keys())
            regs.sort()
            for idx, reg_name in enumerate(regs):
                reg_addr = idx
                width = core.registers[reg_name].width
                addr = interconnect.get_config_addr(reg_addr, base_feat_addr,
                                                    x, y)
                result.append({
                    "name": reg_name,
                    "addr": addr,
                    "range": 1 << width
                })

            # SRAM
            for sram_index in range(4):
                for reg_addr in range(256):
                    addr = \
                        interconnect.get_config_addr(
                            reg_addr, base_feat_addr + sram_index, x, y)
                    result.append({
                        "name": f"SRAM_{sram_index}_{reg_addr}",
                        "addr": addr,
                        "range": 1 << 16
                    })
    return result
