"""garnet.py's flags reach create_cgra() with the values they say (cgra/util_onyx.py get_cc_args).

`args.add_pd = not args.no_pd,` (a trailing comma) made add_pd a 1-tuple, which is always
truthy, so `--no-pd` built power domains anyway (2023-11 until 2026-10-18).
"""
import inspect
import sys

import pytest

# create_cgra() parameter -> the garnet.py flag that turns it off
OFF_FLAGS = {
    "add_pd": "--no-pd",
    "add_pond": "--no-pond",
    "pond_area_opt": "--no-pond-area-opt",
    "pond_area_opt_dual_config": "--no-pond-area-opt-dual-config",
}


class _Stop(Exception):
    pass


def _parse(monkeypatch, *flags):
    import garnet
    monkeypatch.setattr(sys, "argv", ["garnet.py", "--width", "4", "--height", "2",
                                      "--interconnect-only", *flags])
    return garnet.parse_args()


def _cc_kwargs(monkeypatch, *flags):
    """The keyword arguments Garnet() passes to create_cgra() for `garnet.py <flags>`."""
    import cgra.util
    import garnet
    seen = {}

    def fake_create_cgra(**kwargs):
        seen.update(kwargs)
        raise _Stop

    args, io_sides = _parse(monkeypatch, *flags)
    monkeypatch.setattr(cgra.util, "create_cgra", fake_create_cgra)
    with pytest.raises(_Stop):
        garnet.Garnet(args, io_sides)
    return seen


def _bool_params():
    from cgra.util_onyx import create_cgra
    return [name for name, p in inspect.signature(create_cgra).parameters.items()
            if p.annotation in (bool, "bool")]


def test_every_bool_parameter_is_a_bool(monkeypatch):
    kwargs = _cc_kwargs(monkeypatch, *OFF_FLAGS.values())
    bad = {name: kwargs[name] for name in _bool_params()
           if name in kwargs and not isinstance(kwargs[name], bool)}
    assert not bad, f"create_cgra() bool parameters that garnet.py passes as another type: {bad}"


@pytest.mark.parametrize("param, flag", sorted(OFF_FLAGS.items()))
def test_off_flag_turns_its_parameter_off(monkeypatch, param, flag):
    assert _cc_kwargs(monkeypatch)[param] is True
    assert _cc_kwargs(monkeypatch, flag)[param] is False


def _config_map(interconnect):
    """{tile: {feature: (index, [(register, width)])}} for every feature but the power domain's,
    and the number of power-domain features."""
    from passes.power_domain.pd_pass import PowerDomainConfigReg
    tiles, n_pd = {}, 0
    for xy, tile in interconnect.tile_circuits.items():
        features = {}
        for i, feature in enumerate(tile.features()):
            if isinstance(feature, PowerDomainConfigReg):
                n_pd += 1
                continue
            registers = getattr(feature, "registers", None) or {}
            regs = sorted((name, reg.width) for name, reg in registers.items())
            name = getattr(feature, "instance_name", "")
            features[f"{type(feature).__name__} {name}"] = (i, regs)
        tiles[xy] = (sorted(tile.ports), features)
    return tiles, n_pd


def test_no_pd_drops_only_the_power_domain_register(monkeypatch):
    """`aha pnr` builds its bitstreams with --no-pd, for RTL that `aha regress` builds without
    it, and app bundles recorded with power domains replay on --no-pd tile RTL: every other
    config register keeps its feature index, name and width, and the tile ports are the same."""
    import garnet
    maps = {}
    for flags in ((), ("--no-pd",)):
        maps[flags] = _config_map(garnet.Garnet(*_parse(monkeypatch, *flags)).interconnect)
    (with_pd, n_with), (without_pd, n_without) = maps[()], maps[("--no-pd",)]
    assert n_with > 0 and n_without == 0
    assert with_pd == without_pd
