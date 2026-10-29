"""sweep_specs.py --recipe and the tile-variant configs it builds
(mflowgen/CLAUDE.md "The sweep driver"): stock tiles, the PE pond knob,
Tile_PE's clock, and the parts of the thesis recipes.
"""
import importlib.util
import json
import sys
import zipfile
from argparse import Namespace
from pathlib import Path

import pytest

MFLOWGEN = Path(__file__).resolve().parents[2] / "mflowgen"


@pytest.fixture(scope="module")
def ss():
    spec = importlib.util.spec_from_file_location("sweep_specs", MFLOWGEN / "sweep_specs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def listed(ss, capsys, *argv):
    assert ss.main([*argv, "--list"]) == 0
    return capsys.readouterr().out.split()


def test_stock_and_pond_names(ss):
    name = ss._config_name
    assert name(dict(stock=True, runtime_mode="static")) == "stock"
    assert name(dict(stock=True, pond="spec", runtime_mode="static")) == "stock_specpond"
    assert name(dict(pond="none", runtime_mode="rv")) == "fw4_dw16_sc4096_sp_in2_out2_vc2_nopond_rv"


def test_dense_only_parts_are_gone(ss):
    """garnet --dense-only crashes at HEAD: the stock-fabric switch-box and PE-tile
    parts that used it were removed (2026-10-24); the thesis-fabric recipes build
    those tiles."""
    assert not {"fabric_mem", "pe_tile"} & set(ss.RECIPES)
    assert not {"fabric", "pe_tile"} & set(ss.SPEC_SETS)
    assert ss.RECIPES["thesis"] == ["memtile", "app_power"]


def test_stock_tiles_have_no_rv(ss):
    assert ss._unsupported_reason({"stock": True}, "rv")
    assert ss._unsupported_reason({"stock": True}, "static") is None


def test_bad_knob_values(ss):
    args = ss.build_argparser().parse_args([])
    args.modes = ["static"]
    args.extra_specs = None
    args.replace = False
    ss.SPEC_SETS["_bad"] = [dict(pond="lake")]
    try:
        args.spec_set = "_bad"
        with pytest.raises(SystemExit, match="pond"):
            ss._collect_configs(args)
    finally:
        del ss.SPEC_SETS["_bad"]


def env_for(ss, tmp_path, monkeypatch, cfg, *argv):
    monkeypatch.setenv("LAKE_SPEC_CONFIG", "/inherited.json")
    monkeypatch.setenv("LAKE_SPEC_MODE", "rv")
    args = ss.build_argparser().parse_args(list(argv))
    return ss._tile_env(cfg, tmp_path, args)


def test_tile_env_stock_no_pond(ss, tmp_path, monkeypatch):
    env = env_for(ss, tmp_path, monkeypatch, dict(stock=True, pond="none"))
    assert "LAKE_SPEC_CONFIG" not in env and "LAKE_SPEC_MODE" not in env
    assert env["NO_POND"] == "True"


def test_tile_env_spec_pond(ss, tmp_path, monkeypatch):
    env = env_for(ss, tmp_path, monkeypatch, dict(stock=True, pond="spec"))
    assert env["LAKE_POND_SPEC_CONFIG"] == str(tmp_path / ss.POND_SPEC_FILE)
    assert "NO_POND" not in env and "LAKE_SPEC_CONFIG" not in env


def test_tile_env_spec_config_unchanged(ss, tmp_path, monkeypatch):
    env = env_for(ss, tmp_path, monkeypatch, dict(runtime_mode="rv"))
    assert env["LAKE_SPEC_CONFIG"] == str(tmp_path / "spec_config.json")
    assert env["LAKE_SPEC_MODE"] == "rv"
    assert not {"NO_POND", "LAKE_POND_SPEC_CONFIG"} & set(env)


@pytest.mark.parametrize("graph,key", [("Tile_PE", "clock_period_PE"),
                                       ("Tile_MemCore", "CLOCK_PERIOD")])
def test_clock_goes_to_the_graphs_env_var(ss, tmp_path, monkeypatch, graph, key):
    env = env_for(ss, tmp_path, monkeypatch, dict(stock=True),
                  "--graph", str(MFLOWGEN / graph), "--clock-mhz", "400")
    assert env[key] == "2.5"
    assert not {"CLOCK_PERIOD", "clock_period_PE"} - {key} & set(env)


def test_spec_files_record_the_knobs(ss, tmp_path):
    ss._write_spec_files(dict(stock=True, pond="spec", runtime_mode="static"), tmp_path,
                         "make-this", graph="Tile_PE")
    assert json.loads((tmp_path / "spec_config.json").read_text()) == {}
    # the pond is built from it, so its gating is explicit (off unless the config says)
    assert json.loads((tmp_path / ss.POND_SPEC_FILE).read_text()) == {
        "clock_gate_ports": False, "share_clk_ctr": False}
    meta = json.loads((tmp_path / "sweep_meta.json").read_text())
    assert meta["graph"] == "Tile_PE" and meta["pond"] == "spec" and meta["stock"] is True
    row = ss._sweep_meta(tmp_path, meta["config_name"])
    assert row["graph"] == "Tile_PE" and row["pond"] == "spec"


def test_meta_columns_only_when_present(ss):
    old = [{"config_name": "a"}, {"config_name": "b"}]
    ss._fill_meta_columns(old)
    assert old == [{"config_name": "a"}, {"config_name": "b"}]
    new = [{"config_name": "a", "graph": "Tile_PE"}, {"config_name": "b"}]
    ss._fill_meta_columns(new)
    assert new[1]["graph"] == ""


def test_off_param_change_is_not_stale(ss):
    built = {"no_pond": "False"}
    # added since the step ran, off
    assert ss._off_param_change("knob", built, {"knob": "False"})
    assert ss._off_param_change("lake_pond_spec_config", built, {"lake_pond_spec_config": ""})
    # removed since the step ran, was off (the rtl step's dense_only, 2026-10-24)
    assert ss._off_param_change("dense_only", {"dense_only": "False"}, {})
    # on, or on both sides: a change
    assert not ss._off_param_change("knob", built, {"knob": "True"})
    assert not ss._off_param_change("dense_only", {"dense_only": "True"}, {})
    assert not ss._off_param_change("no_pond", built, {"no_pond": "True"})


def test_stale_check_ignores_a_new_off_param(ss, tmp_path):
    def run_script(path, params):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(f"export {k}={v}\n" for k, v in params.items()))
    run_script(tmp_path / "4-rtl" / "mflowgen-run", {"no_pond": "False"})
    (tmp_path / "4-rtl" / ".execstamp").write_text("")
    run_script(tmp_path / ".mflowgen" / "4-rtl" / "mflowgen-run",
               {"no_pond": "False", "dense_only": "False"})
    assert ss._stale_steps(tmp_path) == []
    run_script(tmp_path / ".mflowgen" / "4-rtl" / "mflowgen-run",
               {"no_pond": "False", "dense_only": "True"})
    assert ss._stale_steps(tmp_path) == [("4-rtl", "dense_only None->True")]
    # a parameter dropped since, off when the step ran
    run_script(tmp_path / "4-rtl" / "mflowgen-run", {"no_pond": "False", "dense_only": "False"})
    run_script(tmp_path / ".mflowgen" / "4-rtl" / "mflowgen-run", {"no_pond": "False"})
    assert ss._stale_steps(tmp_path) == []


def test_recipe_passthrough(ss):
    argv = ["--recipe", "thesis", "--out=/o", "--config-jobs", "4", "--app-bundles", "/b",
            "--zip", "--recipe=memtile", "--out-dir", "/o2", "--zip-slim"]
    assert ss._recipe_passthrough(argv) == ["--config-jobs", "4", "--zip", "--zip-slim"]


def test_recipe_runs_each_part(ss, monkeypatch, tmp_path):
    calls = []
    real_main = ss.main
    monkeypatch.setattr(ss, "main", lambda argv: calls.append(argv) or 0)
    args = ss.build_argparser().parse_args(["--recipe", "thesis", "--out-dir", str(tmp_path),
                                            "--pnr-jobs", "2"])
    assert ss._run_recipe(args, ["--recipe", "thesis", "--out-dir", str(tmp_path),
                                 "--pnr-jobs", "2"]) == 0
    assert [c[-1] for c in calls] == [str(tmp_path / "memtile")]
    for part, c in zip(("memtile",), calls):
        assert c[:len(ss.RECIPE_FLAGS[part])] == ss.RECIPE_FLAGS[part]
        assert c[len(ss.RECIPE_FLAGS[part]):] == ["--pnr-jobs", "2", "--out-dir", str(tmp_path / part)]
    monkeypatch.setattr(ss, "main", real_main)


def test_recipe_part_failure_keeps_going(ss, monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(ss, "main", lambda argv: calls.append(argv) or 1)
    monkeypatch.setattr(ss, "_run_app_power", lambda args, out: calls.append(["app_power"]) or 0)
    args = ss.build_argparser().parse_args(["--recipe", "thesis", "--out-dir", str(tmp_path)])
    assert ss._run_recipe(args, []) == 1
    assert calls[-1] == ["app_power"] and len(calls) == 2


def bundles(root, apps, configs):
    for app in apps:
        for c in configs:
            (root / app / c).mkdir(parents=True)
            (root / app / c / "manifest.json").write_text("{}")


def test_app_power_command(ss, monkeypatch, tmp_path):
    bundles(tmp_path / "b", ["conv_3_3", "gaussian"], ["fw4_dw16_sc8192_sp_in2_out2_vc2"])
    (tmp_path / "b" / "notes").mkdir()
    ran = []
    monkeypatch.setattr(ss.subprocess, "run", lambda cmd, **kw: ran.append(cmd) or Namespace(returncode=0))
    args = ss.build_argparser().parse_args(["--recipe", "app_power", "--out-dir", str(tmp_path),
                                            "--app-bundles", str(tmp_path / "b"), "--zip"])
    assert ss._run_recipe(args, []) == 0
    (cmd,) = ran
    assert cmd[1].endswith("cgra_app_power.py")
    assert cmd[cmd.index("--variants") + 1] == (f"conv_3_3={tmp_path / 'b' / 'conv_3_3'},"
                                                f"gaussian={tmp_path / 'b' / 'gaussian'}")
    assert cmd[cmd.index("--clock-mhz") + 1] == str(ss.APP_POWER_MHZ)
    assert cmd[cmd.index("--out-dir") + 1] == str(tmp_path / "app_power")
    assert "--any-config" in cmd and "--zip" in cmd


def test_app_power_one_app_dir_and_skip(ss, tmp_path):
    bundles(tmp_path, ["conv-3-3"], ["c1"])
    assert ss._app_power_variants(tmp_path / "conv-3-3") == [("conv_3_3", tmp_path / "conv-3-3")]
    args = ss.build_argparser().parse_args(["--recipe", "app_power", "--out-dir", str(tmp_path)])
    assert ss._run_app_power(args, tmp_path / "app_power") == 0   # no --app-bundles: skipped


def test_app_bundles_needs_a_recipe(ss, capsys):
    assert ss.main(["--app-bundles", "/x", "--list"]) == 2


def test_memtile_power_needs_memtile_graph(ss):
    args = ss.build_argparser().parse_args(["--graph", str(MFLOWGEN / "Tile_PE"), "--memtile-power",
                                            "--dry-run"])
    with pytest.raises(SystemExit, match="memtile-power"):
        ss._preflight(args)
    assert ss._memtile_power_targets(dict(stock=True), Namespace(memtile_power=True)) == []


def test_relative_graph_is_made_absolute(ss, capsys, monkeypatch, tmp_path):
    """`mflowgen run --design` runs inside the workspace, so --graph
    ./mflowgen/Tile_PE given from the garnet checkout must reach it absolute."""
    monkeypatch.chdir(MFLOWGEN.parent)
    assert ss.main(["--graph", "./mflowgen/Tile_PE", "--spec-set", "thesis_fabric",
                    "--only", "fw4_dw16_sc4096_sp_in2_out2_vc2_thesis",
                    "--out-dir", str(tmp_path / "out"), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert f"mflowgen run --design {MFLOWGEN / 'Tile_PE'}" in out


def test_dw8_32_64_preset_is_the_thesis_set_at_those_widths(ss, capsys):
    names = listed(ss, capsys, "--spec-set", "thesis", "--data-width", "8,32,64", "--runtime-mode", "static,rv")
    assert len(names) == 24
    assert sorted(ss.PRESETS["dw8_32_64"]) == sorted(names)


def test_thesis_mem_opt_recipe(ss, capsys, tmp_path):
    """thesis_mem_opt: the thesis MemTile with lake's options, all three through PnR:
    static with clock gating, RV with clock gating and the filter path as an 8-deep
    FIFO, RV with clock gating and no filter path. Not part of thesis_fabric."""
    assert listed(ss, capsys, "--spec-set", "thesis_fabric_opt") == ss.PRESETS["thesis_opt_pnr"]
    assert ss.main(ss.RECIPE_FLAGS["thesis_mem_opt"] + ["--out-dir", str(tmp_path), "--list"]) == 0
    assert "3 -> synopsys-pt-timing-signoff" in capsys.readouterr().err
    assert "thesis_mem_opt" not in ss.RECIPES["thesis_fabric"]
    static, ff8, nofp = ss.THESIS_OPT_SPEC_POINTS
    for cfg, keys in ((static, {"share_clk_ctr": True, "clock_gate_ports": True}),
                      (ff8, {"clock_gate_ports": True, "filter_fifo_depth": 8}),
                      (nofp, {"clock_gate_ports": True, "add_filter_path": False})):
        ws = tmp_path / ss._config_name(cfg)
        ws.mkdir()
        ss._write_spec_files(cfg, ws, "make-this")
        spec = json.loads((ws / "spec_config.json").read_text())
        assert {k: spec[k] for k in keys} == keys and "thesis" not in spec


def test_thesis_opt_recipe_and_one_clock(ss):
    """thesis_opt = the three optimized MemTiles + the thesis PE pair. Every thesis
    tile part builds at one clock, the slowest block's (the PE's; default the
    app-power clock), not each graph's own default (Tile_PE 1.1 ns)."""
    assert ss.RECIPES["thesis_opt"] == ["thesis_mem_opt", "thesis_pe"]
    clocks = {}
    for part in ("thesis_mem", "thesis_pe", "thesis_mem_opt"):
        flags = ss.RECIPE_FLAGS[part]
        clocks[part] = flags[flags.index("--clock-mhz") + 1]
    assert set(clocks.values()) == {str(ss.THESIS_CLOCK_MHZ)} and ss.THESIS_CLOCK_MHZ == ss.APP_POWER_MHZ


def test_thesis_fmax_recipe(ss, capsys, tmp_path):
    """thesis_fmax: synthesis only, over-constrained, no power, for the chosen
    MemTile pair and the PE pair at every data width, with the fixed upstream
    input budget."""
    assert ss.RECIPES["thesis_fmax"] == ["thesis_fmax_mem", "thesis_fmax_pe", "thesis_fmax_pe_regops"]
    for part in ss.RECIPES["thesis_fmax"]:
        flags = ss.RECIPE_FLAGS[part]
        assert flags[flags.index("--clock-mhz") + 1] == str(ss.FMAX_PROBE_MHZ)
        assert flags[flags.index("--stop-after") + 1] == "cadence-genus-synthesis"
        assert flags[flags.index("--i-delay-ns") + 1] == str(ss.THESIS_I_DELAY_NS)
        assert "--memtile-power" not in flags and "--pnr-set" not in flags
        assert ss.main(flags + ["--out-dir", str(tmp_path), "--list"]) == 0
        names = capsys.readouterr()
        n = 4 if part.endswith("regops") else 8
        assert f"{n} -> cadence-genus-synthesis" in names.err
        assert {n.split("_")[1] for n in names.out.split()} == {"dw8", "dw16", "dw32", "dw64"}
        if part.endswith("regops"):
            assert not any(x.endswith("_rv") for x in names.out.split())
    mem = listed(ss, capsys, *ss.RECIPE_FLAGS["thesis_fmax_mem"], "--out-dir", str(tmp_path))
    assert set(ss.PRESETS["thesis_design_point"]) < set(mem)


def test_thesis_dse_sets(ss, capsys, tmp_path):
    """The design-space sweep: every thesis spec plus the extra width points on the
    thesis fabric with the chosen options (static: shared counter + port gating;
    RV: port gating, no filter path); each width has >= 3 RV points; the reduced
    sweep and its PnR roles are subsets of the full one's, so the full sweep can
    top it up in the same directory."""
    full = listed(ss, capsys, "--spec-set", "thesis_dse", "--out-dir", str(tmp_path))
    assert len(full) == len(set(full)) == 246
    for n in full:
        assert n.endswith("_nofp_portcg_thesis_rv" if n.endswith("_rv") else "_sharectr_portcg_thesis")
    for dw in ss.THESIS_WIDTHS:
        assert sum(f"_dw{dw}_" in n and n.endswith("_rv") for n in full) >= 9
    static_specs = {n[:-len("_sharectr_portcg_thesis")] for n in full if not n.endswith("_rv")}
    thesis = set(listed(ss, capsys, "--spec-set", "thesis", "--out-dir", str(tmp_path)))
    assert thesis <= static_specs and len(static_specs - thesis) == len(ss._thesis_width_points())
    P = ss.PRESETS
    for name in ("thesis_design_point", "thesis_dse_val", "thesis_dse_pnr", "thesis_dse_reduced",
                 "thesis_dse_pnr_reduced", "thesis_dse_val_reduced"):
        assert set(P[name]) <= set(full), name
    assert set(P["thesis_dse_val"]) < set(P["thesis_dse_pnr"]) <= set(P["thesis_dse_reduced"])
    assert set(P["thesis_dse_pnr_reduced"]) <= set(P["thesis_dse_pnr"])
    assert set(P["thesis_dse_val_reduced"]) <= set(P["thesis_dse_val"])
    assert set(P["thesis_design_point"]) <= set(P["thesis_dse_val_reduced"])
    fit = set(P["thesis_dse_pnr"]) - set(P["thesis_dse_val"])
    for dw in ss.THESIS_WIDTHS:
        for mode in ("static", "rv"):
            group = {n for n in fit if f"_dw{dw}_" in n and n.endswith("_rv") == (mode == "rv")}
            assert len(group) >= ss.MIN_FIT_POINTS, (dw, mode)
    assert len(P["thesis_dse_pnr"]) == 38 and len(P["thesis_dse_pnr_reduced"]) == 16
    reduced = listed(ss, capsys, *ss.RECIPE_FLAGS["thesis_dse_reduced_mem"], "--clocks-from",
                     str(clock_json(tmp_path)), "--out-dir", str(tmp_path))
    assert 80 <= len(reduced) <= 100


def test_thesis_cmptrim_recipe(ss, capsys, tmp_path):
    """The RV comparison-network trim A/B: the RV design point with and without
    lake's rv_comparator_trim, MemTile (PnR + idle/active power) and PE tile (PnR),
    at the RV dw16 clock; static specs can't take the option."""
    assert ss.RECIPES["thesis_cmptrim"] == ["thesis_cmptrim_mem", "thesis_cmptrim_pe"]
    assert set(ss.RECIPES["thesis_cmptrim"]) <= set(ss.THESIS_CLOCKED_PARTS)
    base = "fw4_dw16_sc4096_sp_in2_out2_vc2_nofp_portcg_thesis_rv"
    assert set(ss.PRESETS["thesis_design_point"]) >= {base}
    for part in ss.RECIPES["thesis_cmptrim"]:
        flags = ss.RECIPE_FLAGS[part]
        assert flags[flags.index("--i-delay-ns") + 1] == str(ss.THESIS_I_DELAY_NS)
        assert ("--memtile-power" in flags) == part.endswith("_mem")
        names = listed(ss, capsys, *flags, "--clocks-from", str(clock_json(tmp_path)),
                       "--out-dir", str(tmp_path))
        assert [n for n in names if n.startswith("fw")] == \
            [base, "fw4_dw16_sc4096_sp_in2_out2_vc2_nofp_portcg_cmptrim_thesis_rv"]
    assert ss._unsupported_reason(dict(rv_comparator_trim=True), "static")
    assert ss._unsupported_reason(dict(rv_comparator_trim=True), "rv") is None
    assert ss._cmp_trim_tag({"one_sided": True, "scalar_width": 8, "barrier_bit": True,
                             "max_level": 3}) == "cmposs8bbl3"
    assert ss._cmp_trim_tag({"max_level": 3}) == "cmpl3"
    assert ss._spec_key(dict(rv_comparator_trim={"max_level": 3})) != ss._spec_key({})


def test_thesis_filter_ab_recipe(ss, capsys, tmp_path):
    """The RV filter-path A/B: five RV geometries, each as the thesis RV MemTile (no
    filter path, the thesis_dse tile) and with the FIFO-8 filter path; MemTile only,
    every build through PnR with idle/active power, at the RV clocks."""
    assert ss.RECIPES["thesis_filter_ab"] == ["thesis_filter_ab_mem"]
    assert set(ss.RECIPES["thesis_filter_ab"]) <= set(ss.THESIS_CLOCKED_PARTS)
    flags = ss.RECIPE_FLAGS["thesis_filter_ab_mem"]
    assert "--memtile-power" in flags and "--pnr-set" not in flags and "--graph" not in flags
    assert flags[flags.index("--i-delay-ns") + 1] == str(ss.THESIS_I_DELAY_NS)
    clocks = ["--clocks-from", str(clock_json(tmp_path)), "--out-dir", str(tmp_path)]
    names = [n for n in listed(ss, capsys, *flags, *clocks) if n.startswith("fw")]
    geos = ["fw4_dw16_sc4096_sp_in2_out2_vc2", "fw4_dw16_sc8192_sp_in2_out2_vc2",
            "fw2_dw16_sc2048_sp_in1_out1_vc2", "fw1_dw16_sc4096_dp_in1_out1",
            "fw4_dw32_sc8192_sp_in2_out2_vc2"]
    assert names == [f"{g}_{fp}_portcg_thesis_rv" for g in geos for fp in ("nofp", "ff8")]
    dse = set(listed(ss, capsys, *ss.RECIPE_FLAGS["thesis_dse_mem"], *clocks))
    assert {n for n in names if "_nofp_" in n} <= dse        # the A side is the DSE's tile
    assert not {n for n in names if "_ff8_" in n} & dse


def clock_json(tmp_path, clocks=None):
    path = tmp_path / "clocks.json"
    path.write_text(json.dumps(clocks or {m: {str(w): 500 + w for w in (8, 16, 32, 64)}
                                          for m in ("static", "rv")}))
    return path


def probe_dir(root, part, rows):
    """A thesis_fmax part's results.csv + correlation.csv: (config, mode, dw,
    graph, synth WNS ps) at the probe clock."""
    d = root / part
    d.mkdir(parents=True)
    with open(d / "results.csv", "w") as f:
        f.write("config_name,runtime_mode,data_width\n")
        f.writelines(f"{c},{m},{dw}\n" for c, m, dw, _, _ in rows)
    with open(d / "correlation.csv", "w") as f:
        f.write("config_name,runtime_mode,clock_period_ns,graph,tile_synth_wns_ps\n")
        f.writelines(f"{c},{m},1.000,{g},{w}\n" for c, m, _, g, w in rows)


def test_clocks_from_probe(ss, tmp_path, monkeypatch, capsys):
    """--clocks-from <thesis_fmax out dir>: each (mode, width) clock is 0.9 x the
    slowest tile's limit (1000 / (period - WNS)), rounded down to 5 MHz; every
    thesis config builds at its own; the table lands in the out dir."""
    probe_dir(tmp_path / "fmax", "thesis_fmax_pe", [
        ("pe16", "static", 16, "Tile_PE", -741.0),   # 1.741 ns -> 574 -> 515
        ("pe16_rv", "rv", 16, "Tile_PE", -594.0),    # 1.594 ns -> 627 -> 560
        ("pe64", "static", 64, "Tile_PE", -1500.0)])  # 2.5 ns -> 400 -> 360
    probe_dir(tmp_path / "fmax", "thesis_fmax_mem", [
        ("m16", "static", 16, "Tile_MemCore", 0.1),
        ("m16_rv", "rv", 16, "Tile_MemCore", -1000.0),  # 2 ns -> 500: the MemTile sets it
        ("m64", "static", 64, "Tile_MemCore", 0.0)])
    table, lines = ss._thesis_clock_table(tmp_path / "fmax")
    assert table == {("static", 16): 515.0, ("rv", 16): 450.0, ("static", 64): 360.0}
    out = tmp_path / "out"
    args = ss.build_argparser().parse_args(["--clocks-from", str(tmp_path / "fmax"),
                                            "--out-dir", str(out)])
    cfgs = [dict(ss.THESIS_WIDTH_POINTS[16], thesis=True, runtime_mode="static"),
            dict(ss.THESIS_WIDTH_POINTS[64], thesis=True, runtime_mode="static"), dict(stock=True)]
    ss._apply_thesis_clocks(cfgs, args)
    assert [c.get("clock_mhz") for c in cfgs] == [515.0, 360.0, None]
    assert json.loads((out / ss.THESIS_CLOCKS_FILE).read_text()) == {
        "rv": {"16": 450.0}, "static": {"16": 515.0, "64": 360.0}}
    env = env_for(ss, tmp_path, monkeypatch, cfgs[0], "--graph", str(MFLOWGEN / "Tile_PE"))
    assert env["clock_period_PE"] == "1.942"
    ss._write_spec_files(cfgs[0], tmp_path, "make-this")
    assert "clock_mhz" not in json.loads((tmp_path / "spec_config.json").read_text())
    # the written table reads back as a --clocks-from JSON
    assert ss._thesis_clock_table(out / ss.THESIS_CLOCKS_FILE)[0] == table
    cfgs = [dict(ss.THESIS_WIDTH_POINTS[32], thesis=True, runtime_mode="rv")]
    with pytest.raises(SystemExit, match="no clock for rv dw32"):
        ss._apply_thesis_clocks(cfgs, args)
    args.clock_mhz = 400
    with pytest.raises(SystemExit, match="pick one"):
        ss._apply_thesis_clocks(cfgs, args)


def test_clocked_recipes_need_clocks_and_share_a_dir(ss, monkeypatch, tmp_path, capsys):
    """thesis_tiles / thesis_dse* refuse to run at the graphs' default clocks; the
    MemTile parts all build into thesis_dse_mem (so later parts top it up)."""
    calls = []
    monkeypatch.setattr(ss, "main", lambda argv: calls.append(argv) or 0)
    for recipe in ("thesis_tiles", "thesis_dse_reduced", "thesis_dse"):
        argv = ["--recipe", recipe, "--out-dir", str(tmp_path)]
        assert ss._run_recipe(ss.build_argparser().parse_args(argv), argv) == 2
        assert "--clocks-from" in capsys.readouterr().err
    assert not calls
    for recipe in ("thesis_tiles", "thesis_dse_reduced", "thesis_dse"):
        argv = ["--recipe", recipe, "--out-dir", str(tmp_path), "--clocks-from", "/c.json"]
        assert ss._run_recipe(ss.build_argparser().parse_args(argv), argv) == 0
    outs = [c[c.index("--out-dir") + 1] for c in calls]
    assert outs == [str(tmp_path / d) for d in ("thesis_dse_mem", "thesis_tiles_pe",
                                                "thesis_dse_mem", "thesis_dse_mem")]
    assert all(c[c.index("--clocks-from") + 1] == "/c.json" for c in calls)


def test_i_delay_reaches_the_constraints(ss, tmp_path, monkeypatch):
    """--i-delay-ns -> TILE_I_DELAY_NS, which both tile SDCs use for the data
    inputs instead of their fraction of the period."""
    env = env_for(ss, tmp_path, monkeypatch, dict(runtime_mode="rv"), "--i-delay-ns", "0.15")
    assert env["TILE_I_DELAY_NS"] == "0.15" and "TILE_I_DELAY_NS" in ss.BUILD_ENV_KEYS
    assert "TILE_I_DELAY_NS" not in env_for(ss, tmp_path, monkeypatch, dict(runtime_mode="rv"))
    for graph in ("Tile_PE", "Tile_MemCore"):
        tcl = (MFLOWGEN / graph / "constraints" / "common.tcl").read_text()
        knob = tcl.index("set i_delay $::env(TILE_I_DELAY_NS)")
        assert knob < tcl.index("set_input_delay -clock ${clock_name} ${i_delay} [all_inputs -no_clocks]")


def test_fits_per_mode_and_width(ss):
    """Rows that record their data width get <mode>_dw<N> fits, used before the
    mode's when they have MIN_FIT_POINTS; each fit's val_* covers the held-out
    rows in its scope, so the pooled and per-width fits compare on the same tiles."""
    def row(name, dw, x, y, role="fit"):
        return {"config_name": name, "runtime_mode": "static", "data_width": dw,
                "pnr_role": role, "tile_synth_cell_area": x, "tile_pnr_total_area": y}
    rows = [row(f"a{i}", 16, x, 2 * x) for i, x in enumerate((1.0, 2.0, 3.0))]
    rows += [row(f"b{i}", 8, x, 3 * x) for i, x in enumerate((1.0, 2.0, 3.0))]
    rows += [row("v8", 8, 4.0, 12.0, "validate"), row("c32", 32, 2.0, 5.0, "synth")]
    table = ss._fit_and_project(rows, fits=(ss.PNR_FITS[0],))
    by = {t["group"]: t for t in table}
    assert set(by) == {"all", "static", "static_dw16", "static_dw8"}
    v8, c32 = rows[-2], rows[-1]
    assert v8["tile_pnr_total_area_proj_fit"] == "static_dw8"
    assert abs(v8["tile_pnr_total_area_proj"] - 12.0) < 1e-9
    assert c32["tile_pnr_total_area_proj_fit"] == "static"   # no dw32 fit: the mode's
    assert by["static_dw8"]["val_n"] == by["static"]["val_n"] == 1
    assert by["static_dw16"]["val_n"] == 0
    assert by["static_dw8"]["val_max_abs_pct_err"] < by["static"]["val_max_abs_pct_err"]


def test_fmax_estimates(ss):
    assert ss._fmax_estimates({"clock_period_ns": 1.0, "tile_synth_wns_ps": -250.0,
                               "tile_pnr_setup_wns_ns": 0.5}) == {
        "tile_synth_fmax_mhz": 800.0, "tile_pnr_fmax_mhz": 2000.0}
    assert ss._fmax_estimates({"clock_period_ns": None}) == {
        "tile_synth_fmax_mhz": None, "tile_pnr_fmax_mhz": None}


def test_thesis_memtiles_get_power(ss, capsys, tmp_path):
    """The thesis MemTile recipes run the idle/active power tests (their test
    generator builds the thesis fabric); the PE part has none (Tile_PE)."""
    for part in ("thesis_mem", "thesis_mem_opt"):
        assert "--memtile-power" in ss.RECIPE_FLAGS[part]
    assert "--memtile-power" not in ss.RECIPE_FLAGS["thesis_pe"]
    assert ss.main(ss.RECIPE_FLAGS["thesis_mem_opt"] + ["--out-dir", str(tmp_path), "--list"]) == 0
    assert "memtile-power-pnr-idle" in capsys.readouterr().err


def test_fresh_moves_a_busy_workspace_aside(ss, tmp_path, monkeypatch):
    """--fresh on NFS: a file another process holds open can't be removed (EBUSY on
    its .nfsXXXX); the workspace is moved aside so the build starts empty instead
    of the sweep dying."""
    ws = tmp_path / "cfg"
    (ws / "sub").mkdir(parents=True)
    (ws / "sub" / ".nfs000busy").write_text("x")
    real = ss.shutil.rmtree
    calls = []

    def busy_once(path, *a, **kw):
        calls.append(path)
        if len(calls) == 1:
            raise OSError(16, "Device or resource busy", ".nfs000busy")
        return real(path, *a, **kw)
    monkeypatch.setattr(ss.shutil, "rmtree", busy_once)
    ss._fresh_remove(ws)
    assert not ws.exists()
    assert len(calls) == 2 and calls[1].name.startswith("cfg.stale-")
    plain = tmp_path / "plain"
    plain.mkdir()
    ss._fresh_remove(plain)   # a removable workspace is simply removed
    assert not plain.exists() and len(calls) == 3


def test_no_filter_path_knob(ss):
    base = dict(storage_capacity=4096, add_filter_path=False)
    assert ss._config_name(dict(base, runtime_mode="rv")) == "fw4_dw16_sc4096_sp_in2_out2_vc2_nofp_rv"
    assert ss._unsupported_reason(base, "rv") is None
    assert "build_spec_rv" in ss._unsupported_reason(base, "static")
    assert ss._unsupported_reason(dict(base, filter_fifo_depth=8), "rv")
    # unset = the filter path as built: names and spec identity unchanged
    assert ss._config_name(dict(storage_capacity=4096, runtime_mode="rv")) == "fw4_dw16_sc4096_sp_in2_out2_vc2_rv"
    assert ss._spec_key({}) == ss._spec_key({"add_filter_path": True})


@pytest.mark.parametrize("extra, summary", [
    ([], ["36 -> synopsys-pt-timing-signoff", "160 -> cadence-genus-synthesis",
          "PnR model: fit on 8, validated on 28 held-out"]),
    (["--preset", "dw8_32_64"], ["24 -> synopsys-pt-timing-signoff", "PnR model: fit on 0, validated on 24 held-out"]),
    (["--preset", "memtile_pnr"], ["36 -> synopsys-pt-timing-signoff", "PnR model: fit on 8, validated on 28 held-out"]),
])
def test_memtile_recipe_pnr_at_every_width_dw16_fit_only(ss, capsys, tmp_path, extra, summary):
    """The memtile part builds every dw 8/32/64 config through PnR, held out
    of the synth->PnR fit, which stays the 8 dw16_fit8 configs."""
    assert ss.main(ss.RECIPE_FLAGS["memtile"] + extra + ["--out-dir", str(tmp_path), "--list"]) == 0
    err = capsys.readouterr().err
    for line in summary:
        assert line in err


def test_zip_has_pnr_and_synth_reports(ss, tmp_path, monkeypatch):
    """--zip carries every Innovus step's reports (timeDesign's per-group .tarpt
    path reports, not only signoff.summary) and every Genus report; a report over
    REPORT_ZIP_MAX is left out, not the whole zip."""
    ws = tmp_path / "out" / "cfg"
    reports = ["24-cadence-innovus-signoff/reports/signoff.summary",
               "24-cadence-innovus-signoff/reports/signoff_in2reg.tarpt",
               "24-cadence-innovus-signoff/reports/timingReports/signoff_all.tarpt.gz",
               "20-cadence-innovus-cts/reports/cts.summary",
               "19-cadence-innovus-place/reports/place.congestion.rpt",
               "14-cadence-genus-synthesis/reports/qor.rpt",
               "14-cadence-genus-synthesis/results_syn/final_time_default_c.rpt",
               "14-cadence-genus-synthesis/results_syn/syn_power.rpt"]
    for r in reports + ["spec_config.json", "22-cadence-innovus-route/reports/huge.tarpt",
                        "22-cadence-innovus-route/outputs/design.def"]:
        (ws / r).parent.mkdir(parents=True, exist_ok=True)
        (ws / r).write_text("x" * (100 if "huge" in r else 1))
    monkeypatch.setattr(ss, "REPORT_ZIP_MAX", 50)
    args = Namespace(zip_slim=True, zip_path=str(tmp_path / "out.zip"), dry_run=False)
    assert ss._zip_results(tmp_path / "out", None, args)
    names = {n.split("/", 1)[1] for n in zipfile.ZipFile(tmp_path / "out.zip").namelist()}
    assert {f"cfg/{r}" for r in reports} <= names
    assert "cfg/22-cadence-innovus-route/reports/huge.tarpt" not in names
    assert "cfg/22-cadence-innovus-route/outputs/design.def" not in names


def test_rtl_only_memtile_power_makes_the_container_steps(ss, capsys, tmp_path):
    """--rtl-only --memtile-power makes rtl + memtile-power-test-gen (the two
    docker steps) on the full run's graph, so the full run needs no docker."""
    argv = ss.RECIPE_FLAGS["memtile"] + ["--preset", "memtile_pnr", "--out-dir", str(tmp_path)]
    assert ss.main(argv + ["--rtl-only", "--list"]) == 0
    assert "36 -> rtl memtile-power-test-gen" in capsys.readouterr().err
    assert ss.main(argv + ["--rtl-only", "--only", "fw4_dw32_sc8192_sp_in2_out2_vc2", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "DRY-RUN cmd: make rtl" in out
    assert "DRY-RUN cmd: make memtile-power-test-gen" in out
    assert "MEMTILE_POWER" in out
    # The full run's settings (what --skip-existing compares) don't depend on --rtl-only.
    args = ss.build_argparser().parse_args(argv)
    cfg = dict(storage_capacity=8192, data_width=32, vec_width=4, in_ports=2, out_ports=2, vec_capacity=2,
               runtime_mode="static")
    full = ss._build_settings(ss._tile_env(cfg, tmp_path, args))
    args.rtl_only = True
    assert ss._build_settings(ss._tile_env(cfg, tmp_path, args)) == full


def test_registered_operands_only_for_static_thesis_pes(ss, tmp_path, monkeypatch):
    """--pe-registered-operands: static apps register every routed operand (MetaMapper
    PipelinePEs -> RegisterMode DELAY), so a static thesis PE is timed with the bypass arc
    false and the next tile's input as an output budget; RV PEs (FIFO-registered inputs
    feeding the bypass) and MemTiles are unchanged."""
    pe = ["--graph", str(MFLOWGEN / "Tile_PE"), "--pe-registered-operands"]
    static = dict(ss.THESIS_WIDTH_POINTS[16], thesis=True, runtime_mode="static")
    env = env_for(ss, tmp_path, monkeypatch, static, *pe)
    assert env["PE_OPERANDS_REGISTERED"] == "1" and env["TILE_O_DELAY_NS"] == str(ss.THESIS_O_DELAY_NS)
    for cfg, argv in ((dict(static, runtime_mode="rv"), pe), (static, pe[2:]), (static, pe[:2])):
        env = env_for(ss, tmp_path, monkeypatch, cfg, *argv)
        assert "PE_OPERANDS_REGISTERED" not in env and "TILE_O_DELAY_NS" not in env
    assert {"PE_OPERANDS_REGISTERED", "TILE_O_DELAY_NS"} <= set(ss.BUILD_ENV_KEYS)
    assert "--pe-registered-operands" in ss.RECIPE_FLAGS["thesis_tiles_pe"]
    tcl = (MFLOWGEN / "Tile_PE" / "constraints" / "constraints.tcl").read_text()
    assert "set_false_path -through $rm_in -through $rm_out" in tcl and "RegisterMode_inst*/value*" in tcl
    common = (MFLOWGEN / "Tile_PE" / "constraints" / "common.tcl").read_text()
    assert "set tile_o_delay $::env(TILE_O_DELAY_NS)" in common
    assert "${sb_delay} + ${i_delay} + ${o_delay} + ${tile_o_delay}]" in common


def test_regops_probe_replaces_the_static_pe_limit(ss, tmp_path):
    """--clocks-from: a thesis_fmax_pe_regops sweep's static PE limit replaces the bypass-path
    one from thesis_fmax_pe (it is higher), RV and MemTile limits stay."""
    probe_dir(tmp_path / "fmax", "thesis_fmax_pe", [
        ("pe16", "static", 16, "Tile_PE", -826.0),     # bypass path: 1.826 ns -> 547 -> 490
        ("pe16_rv", "rv", 16, "Tile_PE", -566.0)])     # 1.566 ns -> 638 -> 570
    probe_dir(tmp_path / "fmax", "thesis_fmax_mem", [("m16", "static", 16, "Tile_MemCore", 0.0)])
    probe_dir(tmp_path / "fmax", "thesis_fmax_pe_regops", [
        ("pe16", "static", 16, "Tile_PE", -580.0)])    # registered: 1.58 ns -> 632 -> 565
    table, lines = ss._thesis_clock_table(tmp_path / "fmax")
    assert table == {("static", 16): 565.0, ("rv", 16): 570.0}
