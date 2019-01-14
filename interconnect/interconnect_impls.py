from interconnect_graph import *
from switch_box_impls import DisjointSwitchBox


class CGRAInterconnectGraph(InterconnectGraph):
    def __init__(self, bit_width: int, num_tracks: int, height: int,
                 width: int):
        super().__init__()

        self.width = width
        self.height = height

        def connect_tiles(tile0, s0, tile1, s1):
            pass

        for x in range(width):
            for y in range(height):
                sb = DisjointSwitchBox(bit_width, num_tracks)
                tile = Tile(bit_width, sb)
                self.mesh[(x, y)] = tile
                if x > 0:
                    connect_tiles(self.mesh[(x - 1, y)], Side.EAST,
                                  self.mesh[(x, y)], Side.WEST)
                if y > 0:
                    connect_tiles(self.mesh[(x, y - 1)], Side.SOUTH,
                                  self.mesh[(x, y)], Side.NORTH)

    def set_tile(self, x: int, y: int, tile: Tile):
        raise NotImplementedError()

    def set_core(self, x: int, y: int, core: CoreInterface):
        self.get_tile(x, y).set_core(core)

        # TODO(rsetaluri): Wire up core inputs/outputs.
