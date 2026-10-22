"""The thesis CGRA fabrics: static-dense vs ready-valid-dense, for a fair comparison.

garnet.py --thesis {static,rv} builds the CGRA with create_cgra_thesis() instead of
cgra/util_onyx.py create_cgra(). Both fabrics carry only the hardware their mode uses:

static: no FIFOs and no ready-valid anywhere. Switch-box tracks are a plain pipeline
    register plus a bypass mux (the static compiler's delay matching), data tracks are
    data_width bits, the PE is OnyxDensePE (lassen PE, no FIFOs), the MEM tile is the
    static lake spec with plain static ports (no port FIFOs, no bypass config), the
    pond is the static lake-spec pond, the IO tile registers each direction once.
rv: ready-valid with no FIFO bypass. Switch-box tracks are a 2-deep FIFO (always a
    FIFO: no plain-register mode, which would drop tokens on a route) plus the
    bypass mux, data tracks are data_width bits plus separate ready/valid (no sparse
    end-of-stream bit), every PE/MEM/pond port has its tile FIFO and no bypass config
    (the PE keeps its configurable primitive output FIFO), the PE is OnyxDenseRVPE, the
    MEM tile the RV lake spec, the pond the RV lake-spec pond, the IO tile the RV IO.

Neither fabric has sparse cores. The layout, switch boxes, global signals and GLB are
the same as the default (cgra/util_onyx.py) fabric's.
"""
import os
from typing import List

import magma as m
from peak import family
from canal.cyclone import SwitchBoxSide, SwitchBoxIO
from canal.global_signal import GlobalSignalWiring, apply_global_meso_wiring
from canal.util import IOSide, get_array_size, create_uniform_interconnect, SwitchBoxType
from canal.interconnect import Interconnect
from lassen.sim import gen_PE_fc
from lake.modules.onyx_dense_pe import OnyxDensePE
from lake.modules.onyx_dense_rv_pe import OnyxDenseRVPE
from lake.modules.strg_RAM import StrgRAM
from lake.modules.strg_RAM_rv import StrgRAMRV
from lake.modules.stencil_valid import StencilValid
from lake.spec.spec_memory_controller import SpecMemoryController, build_spec, build_spec_rv, \
    build_cgra_pond, resolve_cgra_pond_params
from io_core.io_core_magma import IOCore, IOCoreBase
from memory_core.io_core_rv import IOCoreReadyValid
from memory_core.core_combiner_core import CoreCombinerCore
from passes.power_domain.pd_pass import add_power_domain, add_aon_read_config_data
from passes.tile_id_pass.tile_id_pass import tile_id_physical
from passes.clk_pass.clk_pass import clk_physical
from passes.pipeline_global_pass.pipeline_global_pass import pipeline_global_signals
from passes.interconnect_port_pass import wire_core_flush_pass
from cgra.util_onyx import get_actual_size, load_pond_spec_params

THESIS_MODES = ("static", "rv")


def load_spec_params(path=None):
    """The lake spec of the MEM tile (path, else LAKE_SPEC_CONFIG)."""
    import json
    path = path if path is not None else os.environ.get("LAKE_SPEC_CONFIG", "")
    if not path:
        raise ValueError("a thesis fabric needs a lake spec (--lake-spec-config / LAKE_SPEC_CONFIG)")
    with open(path) as f:
        return json.load(f)


def create_cgra_thesis(mode: str,
                       input_width: int, input_height: int, io_sides: List[IOSide],
                       num_tracks: int = 5,
                       reg_addr_width: int = 8,
                       config_data_width: int = 32,
                       tile_id_width: int = 16,
                       mem_ratio=(1, 4),
                       add_pd: bool = True,
                       use_sim_sram: bool = True,
                       dual_port: bool = False,
                       add_pond: bool = True,
                       harden_flush: bool = True,
                       standalone: bool = False,
                       pipeline_config_interval: int = 8,
                       global_signal_wiring: GlobalSignalWiring = GlobalSignalWiring.ParallelMeso,
                       switchbox_type: SwitchBoxType = SwitchBoxType.Imran,
                       pipeline_regs_density: list = None,
                       port_conn_option: list = None,
                       tech_map: str = "GF"):
    assert mode in THESIS_MODES, mode
    rv = mode == "rv"
    spec_params = load_spec_params()
    dw = spec_params.get("data_width", 16)
    mem_width = dw * spec_params.get("vec_width", 1)
    mem_depth = spec_params.get("storage_capacity", 4096) // max(1, mem_width // 8)
    true_dual_port = dual_port

    # Data tracks are dw bits in both fabrics; ready and valid are separate wires
    ready_valid = rv
    bit_widths = [1, dw]
    track_length = 1
    fifo_depth = 2
    physical_sram = not use_sim_sram
    pe_prefix = "PEGEN_"

    # The lassen PE at the fabric width (garnet_PE.v, concatenated into garnet.v)
    pe_child = gen_PE_fc(dw)(family.MagmaFamily())
    m.compile("garnet_PE", pe_child, output="coreir-verilog", coreir_libs={"float_CW"},
              verilog_prefix=pe_prefix)
    m.clear_cachedFunctions()
    m.frontend.coreir_.ResetCoreIR()
    m.generator.reset_generator_cache()
    m.logging.flush_all()

    common = dict(data_width=dw, use_sim_sram=not physical_sram, tech_map_name=tech_map,
                  mem_width=mem_width, mem_depth=mem_depth, fifo_depth=fifo_depth,
                  dual_port=dual_port, true_dual_port=true_dual_port, rf=False,
                  ready_valid=ready_valid, hybrid_policy=mode)

    if rv:
        pe_ctrls = [OnyxDenseRVPE(data_width=dw, fifo_depth=fifo_depth, ext_pe_prefix=pe_prefix)]
        mem_spec = build_spec_rv(**dict(spec_params, comply_17=False))
        strg_ram = StrgRAMRV(data_width=dw, addr_width=dw, memory_width=mem_width,
                             memory_depth=mem_depth, comply_with_17=False)
    else:
        pe_ctrls = [OnyxDensePE(data_width=dw, ext_pe_prefix=pe_prefix)]
        # The MemTile's configuration register space holds the config (config_passthru)
        mem_spec = build_spec(**dict(spec_params, config_passthru=True, comply_17=False))
        strg_ram = StrgRAM(data_width=dw, addr_width=dw, memory_width=mem_width,
                           memory_depth=mem_depth, comply_with_17=False)
    mem_ctrls = [SpecMemoryController(spec=mem_spec), strg_ram, StencilValid()]

    pe_core = (CoreCombinerCore, dict(common, controllers_list=pe_ctrls, pnr_tag="p",
                                      name="PE", input_prefix="PE_"))
    mem_core = (CoreCombinerCore, dict(common, controllers_list=mem_ctrls, pnr_tag="m",
                                       name="MemCore", input_prefix="MEM_"))
    # Columns repeat mem_ratio: 3 PE columns, then a MEM column
    tile_max = mem_ratio[-1]
    altcore = [pe_core] * (tile_max - mem_ratio[0]) + [mem_core]

    # PE-tile pond: the lake-spec pond of the fabric's mode (LAKE_POND_SPEC_CONFIG
    # geometry, else the default)
    pond_spec_params = None
    if add_pond:
        pond_spec_params = load_pond_spec_params(rv=rv, data_width=dw) or {"data_width": dw}

    def make_pond():
        geom = resolve_cgra_pond_params(pond_spec_params, rv=rv)
        pond_spec = build_cgra_pond(pond_spec_params, rv=rv, comply_17=False)
        pond_cap, pond_dw = geom["storage_capacity"], geom["data_width"]
        # fifo_depth 0: the pond's tile FIFOs are passthroughs (accumulation loops)
        return CoreCombinerCore(data_width=dw,
                                controllers_list=[SpecMemoryController(spec=pond_spec)],
                                use_sim_sram=True,
                                tech_map_name=tech_map,
                                pnr_tag="M",
                                name="PondCore",
                                input_prefix="PondTop_",
                                fifo_depth=0,
                                dual_port=False,
                                rf=True,
                                mem_width=pond_dw,
                                mem_depth=pond_cap // (pond_dw // 8),
                                new_pond=True,
                                ready_valid=ready_valid,
                                hybrid_policy=mode)

    width, height = get_actual_size(input_width, input_height, io_sides)
    x_min, x_max, y_min, y_max = get_array_size(width, height, io_sides)

    cores = {}
    additional_core = {}
    intercore_mapping = None
    for x in range(width):
        for y in range(height):
            in_x = x_min <= x <= x_max
            in_y = y_min <= y <= y_max
            if not in_x and not in_y:
                core = None  # corner
            elif not in_x or not in_y:
                if rv:
                    core = IOCoreReadyValid(data_width=dw, tracks_supported=[1, dw], allow_bypass=False)
                else:
                    core = IOCore(data_width=dw)
            else:
                core_type, core_kwargs = altcore[(x - x_min) % len(altcore)]
                core = core_type(**core_kwargs)
                if add_pond and "alu" in core.get_modes_supported():
                    intercore_mapping = core.get_port_remap()['alu']
                    additional_core[(x, y)] = make_pond()
            cores[(x, y)] = core

    def create_core(xx: int, yy: int):
        return cores[(xx, yy)]

    def create_additional_core(xx: int, yy: int):
        return additional_core.get((xx, yy), None)

    # The pond's output feeds the PE's data inputs and the PE's result feeds the pond
    # inside the tile (the static pond has two writers: update + init)
    inter_core_connection_1 = {}
    inter_core_connection_16 = {}
    if add_pond:
        assert intercore_mapping is not None
        pond_ins = [f"PondTop_input_width_{dw}_num_0"]
        if not rv:
            pond_ins.append(f"PondTop_input_width_{dw}_num_1")
        inter_core_connection_16 = {
            f"PondTop_output_width_{dw}_num_0": [intercore_mapping["data0"],
                                                 intercore_mapping["data1"],
                                                 intercore_mapping["data2"]],
            intercore_mapping["res"]: pond_ins}

    # Core ports connect to every switch-box side; IO tiles connect to the GLB directly
    inputs = set()
    outputs = set()
    for core in cores.values():
        if core is None or isinstance(core, (IOCoreBase, IOCoreReadyValid)):
            continue
        inputs |= {i.qualified_name() for i in core.inputs()}
        outputs |= {o.qualified_name() for o in core.outputs()}
    for core in additional_core.values():
        inputs |= {i.qualified_name() for i in core.inputs()}
        outputs |= {o.qualified_name() for o in core.outputs()}
    if add_pond:
        # The pond output goes to the PE only (inter-core connection)
        outputs.discard(f"PondTop_output_width_{dw}_num_0")

    sides = list(SwitchBoxSide)
    if port_conn_option is not None:
        sides_by_option = {1: sides[:1], 2: sides[:2], 3: sides[:3], 4: sides}
        in_sides = sides_by_option[port_conn_option[0]]
        out_sides = sides_by_option[port_conn_option[1]]
    else:
        in_sides = out_sides = sides
    port_conns = {}
    port_conns.update({p: [(s, SwitchBoxIO.SB_IN) for s in in_sides] for p in inputs})
    port_conns.update({p: [(s, SwitchBoxIO.SB_OUT) for s in out_sides] for p in outputs})

    # A pipeline register (static) / FIFO (RV) on every track and side
    pipeline_regs = []
    if pipeline_regs_density is None:
        for track in range(num_tracks):
            for side in SwitchBoxSide:
                pipeline_regs.append((track, side))
    else:
        for side, n in zip([SwitchBoxSide.NORTH, SwitchBoxSide.SOUTH, SwitchBoxSide.EAST,
                            SwitchBoxSide.WEST], pipeline_regs_density):
            pipeline_regs += [(track, side) for track in range(n)]

    track_list = list(range(num_tracks))
    io_in = {"f2io_1": [0], f"f2io_{dw}": [0]}
    io_out = {"io2f_1": track_list, f"io2f_{dw}": track_list}

    ics = {}
    for bit_width in bit_widths:
        io_conn = None if IOSide.None_ in io_sides else {"in": io_in, "out": io_out}
        inter_core_connection = inter_core_connection_1 if bit_width == 1 else inter_core_connection_16
        ics[bit_width] = create_uniform_interconnect(width, height, bit_width,
                                                     create_core,
                                                     port_conns,
                                                     {track_length: num_tracks},
                                                     switchbox_type,
                                                     pipeline_regs,
                                                     io_sides=io_sides,
                                                     io_conn=io_conn,
                                                     additional_core_fn=create_additional_core,
                                                     inter_core_connection=inter_core_connection)

    # RV: every switch-box register is a 2-deep FIFO, with no pipeline-register mode
    # (canal fifo_only_regs: no fifo_en bit; the register mux is the bypass).
    # The RV pond's write ready depends on its valid (lake: ready is the arbiter grant),
    # which loops with the switch box's valid gating when the pond is fed over the
    # network: its input CB gets a 2-deep FIFO for the network sources (canal
    # input_fifo_ports); the PE result (packed pond) bypasses it.
    input_fifo_ports = [f"PondTop_input_width_{dw}_num_0"] if rv and add_pond else None
    interconnect = Interconnect(ics, reg_addr_width, config_data_width, tile_id_width,
                                lift_ports=standalone,
                                stall_signal_width=1,
                                ready_valid=ready_valid,
                                fifo_only_regs=ready_valid,
                                input_fifo_ports=input_fifo_ports)

    tile_id_physical(interconnect)
    if add_pd:
        add_power_domain(interconnect)
    if harden_flush:
        wire_core_flush_pass(interconnect)

    interconnect.finalize()

    apply_global_meso_wiring(interconnect)
    if add_pd:
        add_aon_read_config_data(interconnect)
    clk_physical(interconnect, 0)
    pipeline_global_signals(interconnect, pipeline_config_interval)

    return interconnect
