from bit_vector import BitVector
from common.dummy_core_magma import DummyCore
from common.testers import BasicTester
from interconnect.interconnect import *
from interconnect.cyclone import RegisterNode
import tempfile
import fault
import fault.random
from interconnect.util import create_uniform_interconnect, SwitchBoxType
import pytest


def assert_tile_coordinate(tile: Tile, x: int, y: int):
    assert tile.x == x and tile.y == y
    for sb in tile.switchbox.get_all_sbs():
        assert_coordinate(sb, x, y)
    for _, node in tile.ports.items():
        assert_coordinate(node, x, y)
    for _, node in tile.switchbox.registers.items():
        assert_coordinate(node, x, y)


def assert_coordinate(node: Node, x: int, y: int):
    assert node.x == x and node.y == y


def insert_reg_ic(ic: InterconnectGraph):
    for pos in ic:
        tile = ic[pos]
        switchbox = tile.switchbox
        for side in SwitchBoxSide:
            for track in range(switchbox.num_track):
                switchbox.add_pipeline_register(side, track)


def find_all_paths(interconnect: Interconnect):
    nodes = interconnect.find_exterior_sb_nodes()
    path_result = []

    def find_all_path_(src: Node, dst: Node, visited: Dict[Node, bool],
                       path: List[Node]):
        if src not in visited:
            visited[src] = True
        path.append(src)

        if src == dst:
            path_result.append(path[:])
        else:
            for n in src:
                if n not in visited or (not visited[n]):
                    find_all_path_(n, dst, visited, path)

        path.pop()
        visited[src] = False

    for node_src in nodes:
        for node_dst in nodes:
            if node_src.x == node_dst.x or node_src.y == node_dst.y:
                continue
            if node_src.width != node_dst.width:
                continue
            node_visited = {}
            path_ = []
            find_all_path_(node_src, node_dst, node_visited, path_)
    return path_result


def merge_path(all_path: List[List[Node]]):
    # merge the path if they don't have overlap
    visited = set()
    merged_path = {}
    for i in range(len(all_path)):
        if i in visited:
            continue
        merged_path[i] = [all_path[i]]
        for j in range(i + 1, len(all_path)):
            if j in visited:
                continue
            path_j = all_path[j]
            is_disjoint = True
            for path_i in merged_path[i]:
                # compute if they have any overlap
                if not set(path_i).isdisjoint(path_j):
                    is_disjoint = False
                    break
            if is_disjoint:
                # we need to merge them
                merged_path[i].append(path_j)
                visited.add(j)

    return merged_path


def generate_config_test_data(interconnect: Interconnect,
                              merged_paths: Dict[int, List[List[Node]]]):
    config_data = []
    test_data = []

    for _, paths in merged_paths.items():
        config_data_entry = []
        test_data_entry = {}
        for path in paths:
            for i in range(len(path) - 1):
                src_node = path[i]
                dst_node = path[i + 1]

                config = interconnect.get_route_bitstream_config(src_node,
                                                                 dst_node)
                if config is not None:
                    config_data_entry.append(config)
            # store the src and dst port
            src_node = path[0]
            dst_node = path[-1]
            num_cycle = 0
            # count how many registers are there
            for node in path:
                if isinstance(node, RegisterNode):
                    num_cycle += 1
            test_data_path = (src_node, dst_node,
                              fault.random.random_bv(src_node.width))
            if num_cycle not in test_data_entry:
                test_data_entry[num_cycle] = [test_data_path]
            else:
                test_data_entry[num_cycle].append(test_data_path)

        # we pre-process it so that the number of clock cycle delay will
        # be incremental for each entry
        clocks = list(test_data_entry.keys())
        clocks.sort()
        pre_clk = clocks[0]
        clk_test_data = []
        for i in range(len(clocks)):
            num_clk = clocks[i] - pre_clk
            clk_test_data.append((num_clk, test_data_entry[clocks[i]]))
            pre_clk = clocks[i]
        test_data.append(clk_test_data)
    assert len(config_data) == len(test_data)
    return config_data, test_data


@pytest.mark.parametrize("num_tracks", [2, 4])
@pytest.mark.parametrize("chip_size", [2, 4])
@pytest.mark.parametrize("reg_mode", [True, False])
def _test_interconnect(num_tracks: int, chip_size: int, reg_mode: bool):
    addr_width = 8
    data_width = 32
    bit_widths = [1, 16]

    tile_id_width = 16

    track_length = 1

    # creates all the cores here
    # we don't want duplicated cores when snapping into different interconnect
    # graphs
    cores = {}
    for x in range(chip_size):
        for y in range(chip_size):
            cores[(x, y)] = DummyCore()

    def create_core(xx: int, yy: int):
        return cores[(xx, yy)]

    in_conn = []
    out_conn = []
    for side in SwitchBoxSide:
        in_conn.append((side, SwitchBoxIO.SB_IN))
        out_conn.append((side, SwitchBoxIO.SB_OUT))

    ics = {}
    for bit_width in bit_widths:
        ic = create_uniform_interconnect(chip_size, chip_size, bit_width,
                                         create_core,
                                         {f"data_in_{bit_width}b": in_conn,
                                          f"data_out_{bit_width}b": out_conn},
                                         {track_length: num_tracks},
                                         SwitchBoxType.Disjoint)
        ics[bit_width] = ic

        # if reg_mode is one, insert switchbox everywhere
        if reg_mode:
            insert_reg_ic(ic)

    interconnect = Interconnect(ics, addr_width, data_width, tile_id_width,
                                lift_ports=True, fan_out_config=True)

    # assert tile coordinates
    for (x, y), tile_circuit in interconnect.tile_circuits.items():
        for _, tile in tile_circuit.tiles.items():
            assert_tile_coordinate(tile, x, y)

    all_path = find_all_paths(interconnect)
    merged_path = merge_path(all_path)
    config_data, test_data = generate_config_test_data(interconnect,
                                                       merged_path)

    circuit = interconnect.circuit()
    tester = BasicTester(circuit, circuit.clk, circuit.reset)

    # the actual test
    assert len(config_data) == len(test_data)
    # NOTE:
    # we don't test the configuration read here
    for i in range(len(config_data)):
        tester.reset()
        for addr, index in config_data[i]:
            tester.configure(BitVector(addr, data_width), index)
        # poke the data
        for _, test_entry in test_data:
            for input_port, _, value in test_entry:
                tester.poke(input_port, value)
                tester.eval()
        # step the clocks and check the values
        for num_clk, test_entry in test_data:
            for _ in range(num_clk):
                tester.step(2)
            for _, output_port, value in test_entry:
                tester.expect(output_port, value)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])


def _test_dump_pnr():
    num_tracks = 2
    addr_width = 8
    data_width = 32
    bit_widths = [1, 16]

    tile_id_width = 16

    chip_size = 2
    track_length = 1

    # creates all the cores here
    # we don't want duplicated cores when snapping into different interconnect
    # graphs
    cores = {}
    for x in range(chip_size):
        for y in range(chip_size):
            cores[(x, y)] = DummyCore()

    def create_core(xx: int, yy: int):
        return cores[(xx, yy)]

    in_conn = []
    out_conn = []
    for side in SwitchBoxSide:
        in_conn.append((side, SwitchBoxIO.SB_IN))
        out_conn.append((side, SwitchBoxIO.SB_OUT))

    ics = {}
    for bit_width in bit_widths:
        ic = create_uniform_interconnect(chip_size, chip_size, bit_width,
                                         create_core,
                                         {f"data_in_{bit_width}b": in_conn,
                                          f"data_out_{bit_width}b": out_conn},
                                         {track_length: num_tracks},
                                         SwitchBoxType.Disjoint)
        ics[bit_width] = ic

    interconnect = Interconnect(ics, addr_width, data_width, tile_id_width,
                                lift_ports=True, fan_out_config=True)

    design_name = "test"
    with tempfile.TemporaryDirectory() as tempdir:
        interconnect.dump_pnr(tempdir, design_name)

        assert os.path.isfile(os.path.join(tempdir, f"{design_name}.info"))
        assert os.path.isfile(os.path.join(tempdir, "1.graph"))
        assert os.path.isfile(os.path.join(tempdir, "16.graph"))

# _test_interconnect(2, 2, True)
