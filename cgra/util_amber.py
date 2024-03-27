from canal.cyclone import SwitchBoxSide, SwitchBoxIO
from canal.global_signal import GlobalSignalWiring, apply_global_meso_wiring,\
    apply_global_fanout_wiring, apply_global_parallel_meso_wiring
from canal.util import IOSide, get_array_size, create_uniform_interconnect, \
    SwitchBoxType
from canal.interconnect import Interconnect
from passes_amber.power_domain.pd_pass import add_power_domain, add_aon_read_config_data
from lassen.sim import PE_fc as lassen_fc
from io_core.io_core_magma import IOCoreValid, IOCore
from memory_core.memory_core_magma import MemCore
from memory_core.pond_core import PondCore
from peak_core.peak_core import PeakCore
from typing import Tuple, Dict, List, Tuple
from passes_amber.tile_id_pass.tile_id_pass import tile_id_physical
from passes_amber.clk_pass.clk_pass import clk_physical
from passes_amber.pipeline_global_pass.pipeline_global_pass import pipeline_global_signals
from passes_amber.interconnect_port_pass import wire_core_flush_pass
from gemstone.common.util import compress_config_data
from peak_gen.peak_wrapper import wrapped_peak_class
from peak_gen.arch import read_arch


def get_actual_size(width: int, height: int, io_sides: IOSide):
    if io_sides & IOSide.North:
        height += 1
    if io_sides & IOSide.East:
        width += 1
    if io_sides & IOSide.South:
        height += 1
    if io_sides & IOSide.West:
        width += 1
    return width, height


def create_cgra(width: int, height: int, io_sides: IOSide,
                add_reg: bool = True,
                mem_ratio: Tuple[int, int] = (1, 4),
                reg_addr_width: int = 8,
                config_data_width: int = 32,
                tile_id_width: int = 16,
                num_tracks: int = 5,
                add_pd: bool = True,
                use_sim_sram: bool = True,
                hi_lo_tile_id: bool = True,
                pass_through_clk: bool = True,
                tile_layout_option: int = 0,  # 0: column-based, 1: row-based
                global_signal_wiring: GlobalSignalWiring =
                GlobalSignalWiring.Meso,
                pipeline_config_interval: int = 8,
                standalone: bool = False,
                add_pond: bool = False,
                pond_area_opt: bool = True,
                pond_area_opt_share: bool = False,
                pond_area_opt_dual_config: bool = True,
                harden_flush: bool = True,
                use_io_valid: bool = True,
                switchbox_type: SwitchBoxType = SwitchBoxType.Imran,
                pipeline_regs_density: list = None,
                port_conn_option: list = None,
                port_conn_override: Dict[str,
                                         List[Tuple[SwitchBoxSide,
                                                    SwitchBoxIO]]] = None,
                pe_fc=lassen_fc,
                ready_valid: bool = False):
    # currently only add 16bit io cores
    bit_widths = [1, 16]
    track_length = 1

    # compute the actual size
    width, height = get_actual_size(width, height, io_sides)
    # these values are inclusive
    x_min, x_max, y_min, y_max = get_array_size(width, height, io_sides)
    # compute ratio
    tile_max = mem_ratio[-1]
    mem_tile_ratio = tile_max - mem_ratio[0]

    # creates all the cores here
    # we don't want duplicated cores when snapping into different interconnect
    # graphs
    cores = {}
    additional_core = {}
    for x in range(width):
        for y in range(height):
            # empty corner
            if x in range(x_min) and y in range(y_min):
                core = None
            elif x in range(x_min) and y in range(y_max + 1, height):
                core = None
            elif x in range(x_max + 1, width) and y in range(y_min):
                core = None
            elif x in range(x_max + 1, width) and y in range(y_max + 1, height):
                core = None
            elif x in range(x_min) \
                    or x in range(x_max + 1, width) \
                    or y in range(y_min) \
                    or y in range(y_max + 1, height):
                if use_io_valid:
                    core = IOCoreValid(config_addr_width=reg_addr_width,
                                       config_data_width=config_data_width)
                else:
                    core = IOCore()
            else:
                if tile_layout_option == 0:
                    use_mem_core = (x - x_min) % tile_max >= mem_tile_ratio
                elif tile_layout_option == 1:
                    use_mem_core = (y - y_min) % tile_max >= mem_tile_ratio

                if use_mem_core:
                    core = MemCore(use_sim_sram=use_sim_sram, gate_flush=not harden_flush)
                else:
                    core = PeakCore(pe_fc)
                    if add_pond:
                        additional_core[(x, y)] = PondCore(gate_flush=not harden_flush,
                                                           pond_area_opt=pond_area_opt,
                                                           pond_area_opt_share=pond_area_opt_share,
                                                           pond_area_opt_dual_config=pond_area_opt_dual_config)
            cores[(x, y)] = core

    def create_core(xx: int, yy: int):
        return cores[(xx, yy)]

    def create_additional_core(xx: int, yy: int):
        return additional_core.get((xx, yy), None)

    # pond may have inter-core connection
    if add_pond:
        inter_core_connection_1 = {"PondTop_output_width_1_num_0": ["bit0"]}
        inter_core_connection_16 = {"PondTop_output_width_16_num_0": ["data0", "data1"],
                                    "res": ["PondTop_input_width_16_num_0", "PondTop_input_width_16_num_1"]}
    else:
        inter_core_connection = {}

    # Specify input and output port connections.
    inputs = set()
    outputs = set()
    for core in cores.values():
        # Skip IO cores.
        if core is None or isinstance(core, IOCoreValid):
            continue
        inputs |= {i.qualified_name() for i in core.inputs()}
        outputs |= {o.qualified_name() for o in core.outputs()}

    if add_pond:
        for core in additional_core.values():
            inputs |= {i.qualified_name() for i in core.inputs()}
            outputs |= {o.qualified_name() for o in core.outputs()}

            # Pond outputs will be connected to the SBs
            # outputs.remove("data_out_pond")
            # outputs.remove("valid_out_pond")

    # This is slightly different from the original CGRA. Here we connect
    # input to every SB_IN and output to every SB_OUT.
    if port_conn_option is None:
        port_conns = {}
        in_conn = [(side, SwitchBoxIO.SB_IN) for side in SwitchBoxSide]
        out_conn = [(side, SwitchBoxIO.SB_OUT) for side in SwitchBoxSide]
        port_conns.update({input_: in_conn for input_ in inputs})
        port_conns.update({output: out_conn for output in outputs})
    else:
        port_conns = {}
        sb_side_dict = {
            1: [SwitchBoxSide.NORTH],
            2: [SwitchBoxSide.NORTH, SwitchBoxSide.SOUTH],
            3: [SwitchBoxSide.NORTH, SwitchBoxSide.SOUTH, SwitchBoxSide.EAST],
            4: SwitchBoxSide
        }
        [in_option, out_option] = port_conn_option
        in_conn = [(side, SwitchBoxIO.SB_IN) for side in sb_side_dict.get(in_option)]
        out_conn = [(side, SwitchBoxIO.SB_OUT) for side in sb_side_dict.get(out_option)]
        port_conns.update({input_: in_conn for input_ in inputs})
        port_conns.update({output: out_conn for output in outputs})

    if port_conn_override is not None:
        port_conns.update(port_conn_override)

    pipeline_regs = []
    if pipeline_regs_density is None:
        for track in range(num_tracks):
            for side in SwitchBoxSide:
                pipeline_regs.append((track, side))
    else:
        [regs_north, regs_south, regs_east, regs_west] = pipeline_regs_density
        for track in range(regs_north):
            pipeline_regs.append((track, SwitchBoxSide.NORTH))
        for track in range(regs_south):
            pipeline_regs.append((track, SwitchBoxSide.SOUTH))
        for track in range(regs_east):
            pipeline_regs.append((track, SwitchBoxSide.EAST))
        for track in range(regs_west):
            pipeline_regs.append((track, SwitchBoxSide.WEST))
    # if reg mode is off, reset to empty
    if not add_reg:
        pipeline_regs = []
    ics = {}

    track_list = list(range(num_tracks))
    io_in = {"f2io_1": [0], "f2io_16": [0]}
    io_out = {"io2f_1": track_list, "io2f_16": track_list}

    for bit_width in bit_widths:
        if io_sides & IOSide.None_:
            io_conn = None
        else:
            io_conn = {"in": io_in, "out": io_out}
        if bit_width == 1:
            inter_core_connection = inter_core_connection_1
        else:
            inter_core_connection = inter_core_connection_16
        ic = create_uniform_interconnect(width, height, bit_width,
                                         create_core,
                                         port_conns,
                                         {track_length: num_tracks},
                                         switchbox_type,
                                         pipeline_regs,
                                         io_sides=io_sides,
                                         io_conn=io_conn,
                                         additional_core_fn=create_additional_core,
                                         inter_core_connection=inter_core_connection)
        ics[bit_width] = ic

    interconnect = Interconnect(ics, reg_addr_width, config_data_width,
                                tile_id_width,
                                lift_ports=standalone,
                                stall_signal_width=1,
                                ready_valid=ready_valid)
    if hi_lo_tile_id:
        tile_id_physical(interconnect)
    if add_pd:
        add_power_domain(interconnect)

    # add hardened flush signal
    if harden_flush:
        wire_core_flush_pass(interconnect)

    interconnect.finalize()

    if global_signal_wiring == GlobalSignalWiring.Meso:
        apply_global_meso_wiring(interconnect)
    elif global_signal_wiring == GlobalSignalWiring.Fanout:
        apply_global_fanout_wiring(interconnect)
    elif global_signal_wiring == GlobalSignalWiring.ParallelMeso:
        apply_global_meso_wiring(interconnect)
    if add_pd:
        add_aon_read_config_data(interconnect)

    if pass_through_clk:
        clk_physical(interconnect, tile_layout_option)

    pipeline_global_signals(interconnect, pipeline_config_interval)

    return interconnect
