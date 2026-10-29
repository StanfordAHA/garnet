"""The PE-tile pond takes the MEM spec's clock-gating options (cgra/util_onyx.py
with_mem_power_options): lake Spec share_clk_ctr / clock_gate_ports set in the MEM
spec config, true or false, apply to every lake spec in the CGRA, unless the pond's
own JSON sets them; unset, the pond takes lake's defaults (gated since 2026-10-28).
The legacy (non-lake) PondCore can't take them and isn't given them."""
from cgra.util_onyx import SPEC_POWER_OPTIONS, with_mem_power_options

GATED = {"share_clk_ctr": True, "clock_gate_ports": True}


def test_no_options_leaves_the_pond_params_alone():
    for pond in (None, {}, {"storage_capacity": 128}):
        assert with_mem_power_options(pond, None) is pond
        assert with_mem_power_options(pond, {"data_width": 16}) is pond


def test_an_ungated_mem_spec_gives_an_ungated_pond():
    off = {"share_clk_ctr": False, "clock_gate_ports": False}
    assert with_mem_power_options(None, dict(off, data_width=16)) == off
    assert with_mem_power_options({"dims": 6}, {"clock_gate_ports": False}) == {"dims": 6, "clock_gate_ports": False}


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


def test_rv_pond_inherits_the_comparator_trim():
    """lake rv_comparator_trim (SPEC_RV_OPTIONS) reaches an RV pond only: the static
    pond (build_pond) does not take it."""
    trim = {"rv_comparator_trim": True}
    assert with_mem_power_options(None, dict(trim, clock_gate_ports=True), rv=True) == \
        dict(trim, clock_gate_ports=True)
    assert with_mem_power_options(None, dict(trim, clock_gate_ports=True)) == {"clock_gate_ports": True}
    pond = {"dims": 6}
    assert with_mem_power_options(pond, trim) is pond
    assert with_mem_power_options({"rv_comparator_trim": False}, trim, rv=True) == {"rv_comparator_trim": False}
