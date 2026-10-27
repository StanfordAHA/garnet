"""mapper/netlist_util.py helpers that need no CGRA build."""


def test_visited_register_pairs_drops_a_pair_as_a_whole():
    from mapper.netlist_util import visited_register_pairs
    # "dead" is a register whose output drives nothing: its source is visited
    # (or not), its sink is not; the pair after it must stay aligned.
    sources = ["a", "dead", "b"]
    sinks = ["A", "DEAD", "B"]
    node_map = {n: n + "'" for n in ["a", "A", "dead", "b", "B"]}
    srcs, snks = visited_register_pairs(sources, sinks, node_map)
    assert srcs == ["a'", "b'"]
    assert snks == ["A'", "B'"]


def test_visited_register_pairs_keeps_everything_when_all_visited():
    from mapper.netlist_util import visited_register_pairs
    sources, sinks = ["a", "b"], ["A", "B"]
    node_map = {n: n.upper() + "x" for n in sources + sinks}
    assert visited_register_pairs(sources, sinks, node_map) == (["Ax", "Bx"], ["Ax", "Bx"])
