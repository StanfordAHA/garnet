"""The PE-tile pond takes the MEM spec's clock-gating options (cgra/util_onyx.py
with_mem_power_options): lake Spec share_clk_ctr / clock_gate_ports set in the MEM
spec config apply to every lake spec in the CGRA, unless the pond's own JSON sets
them. The legacy (non-lake) PondCore can't take them and isn't given them."""
from cgra.util_onyx import SPEC_POWER_OPTIONS, with_mem_power_options

GATED = {"share_clk_ctr": True, "clock_gate_ports": True}


def test_no_options_leaves_the_pond_params_alone():
    for pond in (None, {}, {"storage_capacity": 128}):
        assert with_mem_power_options(pond, None) is pond
        assert with_mem_power_options(pond, {"data_width": 16}) is pond
        assert with_mem_power_options(pond, {"clock_gate_ports": False}) is pond


def test_pond_inherits_the_mem_options():
    assert with_mem_power_options(None, dict(GATED, storage_capacity=4096)) == GATED
    assert with_mem_power_options({"storage_capacity": 128, "dims": 6}, GATED) == \
        {"storage_capacity": 128, "dims": 6, **GATED}


def test_pond_json_wins():
    pond = {"clock_gate_ports": False}
    assert with_mem_power_options(pond, GATED) == {"clock_gate_ports": False, "share_clk_ctr": True}


def test_input_not_mutated():
    pond = {"dims": 6}
    with_mem_power_options(pond, GATED)
    assert pond == {"dims": 6}
    assert set(SPEC_POWER_OPTIONS) == set(GATED)
