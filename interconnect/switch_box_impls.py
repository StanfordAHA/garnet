from interconnect_graph import SwitchBox, Side


class DisjointSwitchBox(SwitchBox):
    def __init__(self, width: int, num_tracks: int):
        connections = []
        for track in range(num_tracks):
            for src_side in Side:
                for dst_side in Side:
                    if dst_side == src_side:
                        continue
                    connections.append((track, src_side, track, dst_side))
        super().__init__(width, num_tracks, connections)


# TODO(rsetaluri): Implement Wilton, Imran SB topologies.
