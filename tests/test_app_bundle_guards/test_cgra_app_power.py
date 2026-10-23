"""mflowgen/cgra_app_power.py (whole-CGRA power of app-bundle variants), its
graph hook common/app_variants.py and gen_app_bundle.py --cgra-tiles: the
parts that run without the build machine (env parsing, tile roles, report
parsing and the per-variant sums)."""
import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

MFLOWGEN = Path(__file__).resolve().parents[2] / "mflowgen"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


av = load(MFLOWGEN / "common" / "app_variants.py", "app_variants")
cap = load(MFLOWGEN / "cgra_app_power.py", "cgra_app_power")
gab = load(MFLOWGEN / "common" / "application" / "gen_app_bundle.py", "gen_app_bundle")


def test_app_bundle_variants_env():
    assert av.app_bundle_variants({}) == []
    assert av.app_bundle_variants({av.ENV: " A=/b/A/cfg , B_2=/b/B/cfg,"}) == [("A", "/b/A/cfg"), ("B_2", "/b/B/cfg")]
    for bad in ("A", "A=", "=x", "A-1=/x", "A=/x,A=/y"):
        with pytest.raises(ValueError):
            av.app_bundle_variants({av.ENV: bad})


ROUTE = """Net ID: e1 Segment Size: 1
Segment: 0 Size: 5
PORT MEM_output_width_1_num_2 (3, 2, 1)
SB (1, 3, 2, 2, 1, 1)
RMUX 2_1 (2, 2, 1)
REG T1_WEST (1, 1, 1, 17)
PORT f2io_1 (1, 0, 1)
"""


def test_route_and_idle_tiles():
    assert gab.route_tiles(ROUTE) == {(3, 2), (2, 2), (1, 1), (1, 0)}
    array = {f"Tile_X{x:02X}_Y{y:02X}": ("Tile_MemCore" if x == 3 else "Tile_PE")
             for x in range(4) for y in range(1, 4)}
    array["Tile_X01_Y00"] = "Tile_IOCoreReadyValid"
    tiles = {"m": [("mem0", 3, 2)], "p": [("pe0", 0, 1)]}
    route = Path(__file__).parent / "_route.txt"
    route.write_text(ROUTE)
    try:
        summary = gab.add_route_and_idle_tiles(tiles, array, route)
    finally:
        route.unlink()
    # (3, 2) is placed; (2, 2), (1, 1) are PE route tiles; (1, 0) is an IO tile
    assert tiles["p"] == [("pe0", 0, 1), ("route", 1, 1), ("route", 2, 2), ("idle", 2, 3)]
    assert tiles["m"] == [("mem0", 3, 2), ("idle", 3, 3)]
    assert summary == {"route": {"Tile_MemCore": 0, "Tile_PE": 2},
                       "idle": {"Tile_MemCore": "Tile_X03_Y03", "Tile_PE": "Tile_X02_Y03"}}


HIER = """Hierarchy                             Power    Power    Power    Power    %
----------------------------------------------------------------------------------
{top}                          {i} {s} {l} {t} 100.0
  MemCore_inst0 (MemCore_inner) 1.0e-03 1.0e-04 1.0e-04 1.2e-03  50.0
"""
CELL = """  a/b/sram_H_0_0 (IN12LP_S1DB_W02048B064M04S2_HB) 1.00e-03 2.00e-04 3.00e-04 1.50e-03 20.0
  a/b/U1 (SC7P5T_INVX1_SSC14R) 1.0e-06 1.0e-06 1.0e-06 3.0e-06 0.0
"""
XRUN = """0 FS + 1 (stop stall_toggle: testbench.stall = 0)
1000 PS + 2 (stop stall_toggle: testbench.stall = 1)
{start} PS + 2 (stop stall_toggle: testbench.stall = 0)
Simulation complete via $finish(2) at time {end} NS + 0
"""


def make_ws(root, variants, tiles, cfg="cfgX"):
    """Fake out-dir: per variant a bundle (tiles lists + manifest) and the
    post-synth-power reports of each tile workspace. tiles: {variant:
    [(design, tile, role, total_W, window_ns)]}"""
    bundles = {}
    for v in variants:
        b = root / "bundles" / v / cfg
        b.mkdir(parents=True)
        for design in ("Tile_MemCore", "Tile_PE"):
            lines = [f"{role if role != 'placed' else 'op'},{t[6:8]},{t[10:12]}"
                     for d, t, role, *_ in tiles[v] if d == design]
            (b / f"tiles_{design}.list").write_text("\n".join(lines) + "\n")
        json.dump({"app": "x", "array_tiles": {"Tile_MemCore": 4, "Tile_PE": 12}}, open(b / "manifest.json", "w"))
        bundles[v] = str(b)
    for design in ("Tile_MemCore", "Tile_PE"):
        ws = root / "out" / cfg / design
        ws.mkdir(parents=True)
        json.dump({"config": cfg, "tile": design, "variants": bundles}, open(ws / "run_meta.json", "w"))
        for v in variants:
            step = ws / f"21-post-synth-power-{v}"
            rep = step / "outputs" / "reports"
            rep.mkdir(parents=True)
            for d, t, role, total, win_ns in tiles[v]:
                if d != design:
                    continue
                (rep / f"{t}.hier").write_text(HIER.format(top=design, i=total / 2, s=total / 4, l=total / 4, t=total))
                if d == "Tile_MemCore":
                    (rep / f"{t}.cell").write_text(CELL)
                json.dump({"problems": []}, open(rep / f"{t}.replay.json", "w"))
                sim = step / t / "2-cadence-xcelium-sim"
                sim.mkdir(parents=True)
                (sim / "xrun.log").write_text(XRUN.format(start=2000, end=2 + win_ns))
    return root / "out"


def test_report_parsing_and_sums(tmp_path):
    tiles = {
        "A": [("Tile_MemCore", "Tile_X03_Y02", "placed", 10e-3, 1000),
              ("Tile_MemCore", "Tile_X03_Y03", "idle", 1e-3, 1000),
              ("Tile_PE", "Tile_X00_Y01", "placed", 3e-3, 1000),
              ("Tile_PE", "Tile_X01_Y01", "route", 0.5e-3, 1000),
              ("Tile_PE", "Tile_X02_Y03", "idle", 0.2e-3, 1000)],
        "B": [("Tile_MemCore", "Tile_X03_Y02", "placed", 8e-3, 1100),
              ("Tile_MemCore", "Tile_X03_Y03", "idle", 1e-3, 1100),
              ("Tile_PE", "Tile_X00_Y01", "placed", 3e-3, 1100),
              ("Tile_PE", "Tile_X01_Y01", "route", 0.5e-3, 1100),
              ("Tile_PE", "Tile_X02_Y02", "route", 0.5e-3, 1100),
              ("Tile_PE", "Tile_X02_Y03", "idle", 0.2e-3, 1100)],
    }
    out = make_ws(tmp_path, ["A", "B"], tiles)
    assert cap.replay_window(XRUN.format(start=2000, end=1002)) == pytest.approx(1000e-9)
    # app bundle testbench (garnet 9c8d449f): the SAIF starts at the app_window stop
    log = "3248319 PS + 2 (stop app_window: testbench.saif_window = 1)\n" \
          "Simulation complete via $finish(2) at time 10151069 PS + 0\n"
    assert cap.replay_window(log) == pytest.approx((10151069 - 3248319) * 1e-12)
    assert cap.replay_window("Simulation complete via $finish(2) at time 10 NS + 0\n") is None
    assert cap.cell_power(next(out.glob("*/Tile_MemCore/*-A/outputs/reports/Tile_X03_Y02.cell")),
                          r"^IN12LP_") == (pytest.approx(1.5e-3), 1)
    rows = cap.tile_rows(out, r"^IN12LP_")
    assert len(rows) == 11 and all(r["replay_exact"] for r in rows)
    a, b = cap.summarize(rows, out)
    assert (a["variant"], b["variant"]) == ("A", "B")
    assert a["app_W"] == pytest.approx(13.5e-3)
    assert a["sram_W"] == pytest.approx(1.5e-3)       # placed MEM only; the idle tile's SRAM is in idle_W
    # untouched: MEM 4 - 1 = 3, PE 12 - 2 = 10
    assert (a["Tile_MemCore_idle_n"], a["Tile_PE_idle_n"]) == (3, 10)
    assert a["array_W"] == pytest.approx(13.5e-3 + 3 * 1e-3 + 10 * 0.2e-3)
    assert a["app_J"] == pytest.approx(13.5e-3 * 1000e-9)
    assert b["Tile_PE_idle_n"] == 9
    assert b["app_W"] == pytest.approx(12e-3)
    assert b["d_app_W_pct"] == pytest.approx(100 * (12e-3 - 13.5e-3) / 13.5e-3)
    assert b["d_window_s_pct"] == pytest.approx(10.0)
    cap.write_csv(out / "cgra_power.csv", [a, b])
    assert (out / "cgra_power.csv").read_text().splitlines()[0].startswith("config,variant,app")


def test_report_without_cgra_tiles(tmp_path):
    """Bundles recorded without --cgra-tiles: placed tiles only, no array total."""
    tiles = {"A": [("Tile_MemCore", "Tile_X03_Y02", "placed", 10e-3, 1000),
                   ("Tile_PE", "Tile_X00_Y01", "placed", 3e-3, 1000)]}
    out = make_ws(tmp_path, ["A"], tiles)
    (s,) = cap.summarize(cap.tile_rows(out, r"^IN12LP_"), out)
    assert s["app_W"] == pytest.approx(13e-3)
    assert s["array_W"] is None and s["idle_W"] is None


def test_variants_parse_and_configs(tmp_path):
    for v in ("A", "B"):
        for c in ("c1", "c2"):
            if (v, c) == ("B", "c2"):
                continue
            (tmp_path / v / c).mkdir(parents=True)
            json.dump({"spec_config": {"vec_width": 4}, "mode": "rv"}, open(tmp_path / v / c / "manifest.json", "w"))
    variants = cap.parse_variants(f"A={tmp_path / 'A'},B={tmp_path / 'B'}")
    assert cap.configs_of(variants, []) == ["c1"]
    with pytest.raises(SystemExit):
        cap.configs_of(variants, ["c2"])
    json.dump({"spec_config": {"vec_width": 2}, "mode": "rv"}, open(tmp_path / "B" / "c1" / "manifest.json", "w"))
    with pytest.raises(SystemExit):
        cap.load_manifests(variants, "c1")


rvb = load(MFLOWGEN / "common" / "application" / "hooks" / "rv_balance_branches.py", "rv_balance_branches")


def toy_design():
    """IO -> fork: (a) PE m (mul) -> PE s.data0, (b) delay reg (extra_data 1) -> PE s.data1;
    a constant PE feeds s.data2; s -> output IO."""
    pe = {"genref": "global.PE"}
    reg = lambda x: {"genref": "coreir.reg", "genargs": {"width": ["Int", 16]}, "metadata": {"extra_data": x}}
    return {"top": "global.app", "namespaces": {"global": {"modules": {"app": {
        "instances": {"in": {"genref": "global.IO"}, "out": {"genref": "global.IO"}, "m": dict(pe),
                      "d": reg(1), "s": dict(pe), "c": dict(pe)},
        "connections": [["in.out", "m.data0"], ["in.out", "d.in"], ["m.O0", "s.data0"],
                        ["d.out", "s.data1"], ["c.O0", "s.data2"], ["s.O0", "out.in"],
                        ["self.x", "in.in"], ["out.out", "self.y"]]}}}}}


def test_rv_balance_pads_the_short_branch():
    d = toy_design()
    added, report = rvb.balance(d, pe_stages=3, margin=0)
    mod = d["namespaces"]["global"]["modules"]["app"]
    # m arrives at 3 stages, the delay reg at 1 + 1 (its pre-filled token): s.data1 gets 1 register
    assert added == 1 and report == [("s.data1", 1, 1)]
    (rn,) = [n for n in mod["instances"] if n.startswith("rv_balance_")]
    assert rn == "rv_balance_" + hashlib.md5(b"s.data1").hexdigest()[:8] + "_0"   # named after the input
    r = mod["instances"][rn]
    assert r["genref"] == "coreir.reg" and r["metadata"] == {"extra_data": 0}
    conns = [sorted(c) for c in mod["connections"]]
    assert sorted(["d.out", f"{rn}.in"]) in conns and sorted([f"{rn}.out", "s.data1"]) in conns
    assert sorted(["d.out", "s.data1"]) not in conns
    assert sorted(["c.O0", "s.data2"]) in conns          # constant input untouched
    assert mod["metadata"]["rv_balance"]["registers"] == 1
    with pytest.raises(SystemExit):
        rvb.balance(d, pe_stages=3, margin=0)             # already balanced


def test_rv_balance_margin_and_idempotent_hook(tmp_path, monkeypatch):
    d = toy_design()
    added, _ = rvb.balance(d, pe_stages=5, margin=2)
    assert added == (5 - 2) + 2
    (tmp_path / "design_top.json").write_text(json.dumps(toy_design()))
    for _ in range(2):   # a rerun starts from the saved input, not from its own output
        monkeypatch.setattr(sys, "argv", ["rv_balance_branches.py", str(tmp_path), "--pe-stages", "3"])
        rvb.main()
        mod = json.loads((tmp_path / "design_top.json").read_text())["namespaces"]["global"]["modules"]["app"]
        assert len([n for n in mod["instances"] if n.startswith("rv_balance")]) == 1


rtm = load(MFLOWGEN / "common" / "application" / "rv_throughput.py", "rv_throughput")


def toy_routed(tmp_path, long_regs=6, short_regs=1):
    """IO (0,0) -> fork at SB (1,1): branch to PE (5,5) data0 through long_regs route
    registers, branch to data1 through short_regs; PE -> output IO. The PE also takes a
    constant on data2 from a const PE at (6,6)."""
    lines = ["Net ID: e1 Segment Size: 2", "Segment: 0 Size: 9", "PORT io2f_17 (0, 0, 17)",
             "SB (0, 1, 1, 0, 1, 17)"]
    for i in range(long_regs):
        lines += [f"REG T0_EAST (0, {2 + i}, 1, 17)", f"SB (0, {2 + i}, 1, 0, 1, 17)"]
    lines += ["PORT PE_input_width_17_num_0 (5, 5, 17)", "Segment: 1 Size: 4", "SB (0, 1, 1, 0, 1, 17)"]
    for i in range(short_regs):
        lines += [f"REG T1_SOUTH (1, 1, {2 + i}, 17)", f"SB (1, 1, {2 + i}, 1, 1, 17)"]
    lines += ["PORT PE_input_width_17_num_1 (5, 5, 17)", "",
              "Net ID: e2 Segment Size: 1", "Segment: 0 Size: 3", "PORT PE_output_width_17_num_1 (5, 5, 17)",
              "REG T0_NORTH (0, 5, 4, 17)", "PORT f2io_17 (1, 0, 17)", "",
              "Net ID: e3 Segment Size: 1", "Segment: 0 Size: 3", "PORT PE_output_width_17_num_1 (6, 6, 17)",
              "REG T2_WEST (2, 6, 5, 17)", "PORT PE_input_width_17_num_2 (5, 5, 17)", ""]
    (tmp_path / "design.route").write_text("\n".join(lines) + "\n")
    (tmp_path / "design.place").write_text("Block Name X Y #Block ID\n---\n"
                                           "mac 5 5 #p0\nconst_k 6 6 #p1\nin 0 0 #I0\nout 1 0 #I1\n")
    (tmp_path / "design_top.json").write_text(json.dumps(
        {"top": "global.app", "namespaces": {"global": {"modules": {"app": {"instances": {}, "connections": []}}}}}))
    return rtm.model_of(str(tmp_path))


def test_rv_throughput_fork_imbalance(tmp_path):
    m = toy_routed(tmp_path, long_regs=6, short_regs=1)
    rate, _ = m.run(2000, 500)
    assert rate < 0.9                        # the short branch cannot hold the long one's tokens
    short = next(i for i in m.pes[(5, 5)]["in"] if i[1].endswith("_1"))
    assert dict(rtm.mismatches(m))[short] == 5
    # absolute plan: the short edge's unshared route stage + the 5 it is early
    plan = rtm.balance_plan_abs(m)
    assert rtm.plan_by_instance(m, plan) == {"mac.data1": 6}   # only the short branch is padded
    rtm.insert_stages(m, short, 5)
    assert m.run(2000, 500)[0] >= 0.995 and not any(d for _, d in rtm.mismatches(m))
    balanced = toy_routed(tmp_path, long_regs=3, short_regs=3)
    assert balanced.run(2000, 500)[0] >= 0.995
    assert rtm.placement_of(str(tmp_path)) == {"p0": (5, 5), "p1": (6, 6), "I0": (0, 0), "I1": (1, 0)}


def test_rv_throughput_parity_outfifo(tmp_path):
    """IO forks to PE pa (3,3) -> mac (5,5) data0 and straight to mac data1: the mismatch
    (L + 2 + R - S = 3 stages) is odd, so routing alone cannot close it; pa's primitive
    output FIFO (+1) makes it even (4)."""
    lines = ["Net ID: e1 Segment Size: 2", "Segment: 0 Size: 4", "PORT io2f_17 (0, 0, 17)",
             "SB (0, 1, 1, 0, 1, 17)", "REG T0_EAST (0, 2, 1, 17)", "PORT PE_input_width_17_num_0 (3, 3, 17)",
             "Segment: 1 Size: 3", "SB (0, 1, 1, 0, 1, 17)", "REG T1_SOUTH (1, 1, 2, 17)",
             "PORT PE_input_width_17_num_1 (5, 5, 17)", "",
             "Net ID: e4 Segment Size: 1", "Segment: 0 Size: 3", "PORT PE_output_width_17_num_0 (3, 3, 17)",
             "REG T0_EAST (0, 4, 3, 17)", "PORT PE_input_width_17_num_0 (5, 5, 17)", "",
             "Net ID: e2 Segment Size: 1", "Segment: 0 Size: 3", "PORT PE_output_width_17_num_0 (5, 5, 17)",
             "REG T0_NORTH (0, 5, 4, 17)", "PORT f2io_17 (1, 0, 17)", ""]
    (tmp_path / "design.route").write_text("\n".join(lines) + "\n")
    (tmp_path / "design.place").write_text("Block Name X Y #Block ID\n---\n"
                                           "pa 3 3 #p0\nmac 5 5 #p1\nin 0 0 #I0\nout 1 0 #I1\n")
    (tmp_path / "design_top.json").write_text(json.dumps(
        {"top": "global.app", "namespaces": {"global": {"modules": {"app": {"instances": {}, "connections": []}}}}}))
    m = rtm.model_of(str(tmp_path))
    assert sorted(d for _, d in rtm.mismatches(m)) == [0, 3]
    assert rtm.parity_outfifo(m) == ["pa"] and m.prim_out == {(3, 3)}
    assert sorted(d for _, d in rtm.mismatches(m)) == [0, 4]
    assert rtm.plan_by_instance(m, rtm.balance_plan_abs(m)) == {"mac.data1": 1 + 4}
    short = next(i for i in m.pes[(5, 5)]["in"] if i[1].endswith("_1"))
    rtm.insert_stages(m, short, 4)
    assert m.run(2000, 500)[0] >= 0.995
    assert rtm.outfifo_config(["pa"]) == {"pa": {"input_fifo_bypass": [0, 0, 0], "output_fifo_bypass": 0,
                                                 "prim_outfifo_bypass": 0}}
    rtm.apply_outfifo(m, [])
    assert m.prim_out == set()


def test_zip_has_every_synth_report(tmp_path):
    out = tmp_path / "cap"
    ws = out / "cfg" / "Tile_PE"
    files = ["run_meta.json", "make.log",
             "14-cadence-genus-synthesis/reports/qor.rpt",
             "14-cadence-genus-synthesis/reports/Tile_PE.timing.setup.top100.rpt",
             "14-cadence-genus-synthesis/results_syn/final_time_default_c.rpt",
             "14-cadence-genus-synthesis/results_syn/final_area.rpt"]
    for f in files:
        (ws / f).parent.mkdir(parents=True, exist_ok=True)
        (ws / f).write_text("{}")
    cap.zip_results(cap.parse_args(["--out-dir", str(out), "--report-only"]))
    (zp,) = tmp_path.glob("cap_*.zip")
    names = set(zipfile.ZipFile(zp).namelist())
    assert {f"cap/cfg/Tile_PE/{f}" for f in files} <= names


def test_rv_balance_one_bit_edge():
    """A 1-bit edge (a PE's res_p O1 -> another PE's bit0) is padded with corebit.reg;
    a data edge keeps coreir.reg at the design's width."""
    pe = {"genref": "global.PE"}
    d = {"top": "global.app", "namespaces": {"global": {"modules": {"app": {
        "instances": {"in": {"genref": "global.IO"}, "out": {"genref": "global.IO"}, "a": dict(pe),
                      "s": dict(pe), "k": {"genref": "coreir.const", "genargs": {"width": ["Int", 16]}}},
        "connections": [["in.out", "a.data0"], ["a.O1", "s.bit0"], ["a.O0", "s.data0"],
                        ["k.out", "s.data1"], ["s.O0", "out.in"]]}}}}}
    added, _ = rvb.balance(d, pe_stages=0, margin=0, plan={"s.bit0": 2, "s.data0": 1})
    inst = d["namespaces"]["global"]["modules"]["app"]["instances"]
    bit = [i for n, i in inst.items() if n.startswith("rv_balance_" + hashlib.md5(b"s.bit0").hexdigest()[:8])]
    dat = [i for n, i in inst.items() if n.startswith("rv_balance_" + hashlib.md5(b"s.data0").hexdigest()[:8])]
    assert added == 3 and len(bit) == 2 and len(dat) == 1
    assert all(i["modref"] == "corebit.reg" and i["modargs"]["init"] == ["Bool", False]
               and i["metadata"] == {"extra_data": 0} for i in bit)
    assert dat[0]["genref"] == "coreir.reg" and dat[0]["genargs"]["width"] == ["Int", 16]


def test_rv_balance_pe_to_pe_edge_at_the_fabric_width(monkeypatch):
    """A PE -> PE data edge has no width of its own. The padding register takes
    --data-width, else a netlist width that is not a PE instruction constant: at dw32 a
    mapped netlist's only width-carrying instances can be the 132-bit (36 + 3 * 32)
    instruction constants, and a 132-bit register on a 32-bit PE input kills PnR
    ("Cannot wire together")."""
    def design():
        pe = {"modref": "global.PE"}
        ic = {"genref": "coreir.const", "genargs": {"width": ["Int", 132]}}
        return {"top": "global.app", "namespaces": {"global": {"modules": {"app": {
            "instances": {"in": {"modref": "global.IO"}, "out": {"modref": "global.IO"}, "a": dict(pe),
                          "s": dict(pe), "a_inst": dict(ic), "s_inst": dict(ic)},
            "connections": [["in.out", "a.data0"], ["a.O0", "s.data0"], ["in.out", "s.data1"],
                            ["a_inst.out", "a.inst"], ["s.inst", "s_inst.out"], ["s.O0", "out.in"]]}}}}}

    def pad_width(data_width):
        monkeypatch.setattr(rvb, "DATA_WIDTH", data_width)
        d = design()
        rvb.balance(d, pe_stages=0, margin=0, plan={"s.data0": 1})
        inst = d["namespaces"]["global"]["modules"]["app"]["instances"]
        (r,) = [i for n, i in inst.items() if n.startswith("rv_balance_")]
        return r["genargs"]["width"][1]

    assert pad_width(32) == 32
    assert pad_width(None) == 16   # no data-width instance left once the instruction constants are skipped


def toy_unpipelined(tmp_path):
    """Routes without registers (no EXHAUSTIVE_PIPE): IO -> pa; pa res -> pb -> mac data0;
    pa res_p (1-bit) -> mac bit0 directly; mac res -> output IO, mac res_p -> a pond input."""
    nets = [("e1", "PORT io2f_16 (0, 0, 16)", "PORT PE_input_width_16_num_0 (3, 3, 16)"),
            ("e2", "PORT PE_output_width_16_num_0 (3, 3, 16)", "PORT PE_input_width_16_num_0 (4, 4, 16)"),
            ("e3", "PORT PE_output_width_16_num_0 (4, 4, 16)", "PORT PE_input_width_16_num_0 (5, 5, 16)"),
            ("e4", "PORT PE_output_width_1_num_0 (3, 3, 1)", "PORT PE_input_width_1_num_0 (5, 5, 1)"),
            ("e5", "PORT PE_output_width_16_num_0 (5, 5, 16)", "PORT f2io_16 (1, 0, 16)"),
            ("e6", "PORT PE_output_width_1_num_0 (5, 5, 1)", "PORT PondTop_input_width_16_num_0 (6, 6, 16)")]
    lines = []
    for k, (net, a, b) in enumerate(nets):   # one SB node per net (an SB node is shared by its nets)
        lines += [f"Net ID: {net} Segment Size: 1", "Segment: 0 Size: 3", a, f"SB ({k}, 1, 1, 0, 1, 16)", b, ""]
    (tmp_path / "design.route").write_text("\n".join(lines) + "\n")
    (tmp_path / "design.place").write_text("Block Name X Y #Block ID\n---\n"
                                           "pa 3 3 #p0\npb 4 4 #p1\nmac 5 5 #p2\nin 0 0 #I0\nout 1 0 #I1\n")
    (tmp_path / "design_top.json").write_text(json.dumps(
        {"top": "global.app", "namespaces": {"global": {"modules": {"app": {"instances": {}, "connections": []}}}}}))
    return rtm.model_of(str(tmp_path))


def test_rv_throughput_latency_match_unpipelined(tmp_path):
    m = toy_unpipelined(tmp_path)
    assert m.is_source(("PORT", "PondTop_output_width_16_num_0", 6, 6))
    assert m.is_sink(("PORT", "PondTop_input_width_16_num_0", 6, 6))
    assert len(m.pes[(3, 3)]["out"]) == 2          # pa drives res and res_p
    bit0 = next(i for i in m.pes[(5, 5)]["in"] if "width_1_" in i[1])
    # pa in 1, pa out 2, pb in 3, pb out 4, mac data0 5; mac bit0 3: two stages early
    assert dict(rtm.mismatches(m))[bit0] == 2
    plan = rtm.latency_match_plan(m)
    assert rtm.plan_by_instance(m, plan) == {"mac.bit0": 2}
    assert not any(d for _, d in rtm.mismatches(m))
    assert m.run(2000, 500)[0] >= 0.995           # both of pa's outputs feed mac


def test_min_register_plan_and_shared_chain(tmp_path):
    """IO forks to pa (3,3) and straight to mac1.data1 / mac2.data1; pa -> pb -> mac1.data0
    and mac2.data0. Both direct inputs arrive 4 stages early: 4 registers each, which one
    chain on the IO's output can serve (tapped by both)."""
    def net(name, src, sinks):
        lines = [f"Net ID: {name} Segment Size: {len(sinks)}"]
        for k, s in enumerate(sinks):
            lines += [f"Segment: {k} Size: 3", src, f"SB ({name[1:]}, 1, 1, 0, 1, 16)", s]
        return lines + [""]

    def pe_in(x, k):
        return f"PORT PE_input_width_16_num_{k} ({x}, {x}, 16)"

    def pe_out(x):
        return f"PORT PE_output_width_16_num_0 ({x}, {x}, 16)"
    lines = (net("e1", "PORT io2f_16 (0, 0, 16)", [pe_in(3, 0), pe_in(5, 1), pe_in(6, 1)])
             + net("e2", pe_out(3), [pe_in(4, 0)])
             + net("e3", pe_out(4), [pe_in(5, 0), pe_in(6, 0)])
             + net("e4", pe_out(5), ["PORT f2io_16 (1, 0, 16)"])
             + net("e5", pe_out(6), ["PORT f2io_16 (2, 0, 16)"]))
    (tmp_path / "design.route").write_text("\n".join(lines) + "\n")
    (tmp_path / "design.place").write_text("Block Name X Y #Block ID\n---\npa 3 3 #p0\npb 4 4 #p1\n"
                                           "mac1 5 5 #p2\nmac2 6 6 #p3\nin 0 0 #I0\no1 1 0 #I1\no2 2 0 #I2\n")
    (tmp_path / "design_top.json").write_text(json.dumps(
        {"top": "global.app", "namespaces": {"global": {"modules": {"app": {"instances": {}, "connections": []}}}}}))
    m = rtm.model_of(str(tmp_path))
    plan = rtm.plan_by_instance(m, rtm.min_register_plan(m))
    assert plan == {"mac1.data1": 4, "mac2.data1": 4}
    assert not any(d for _, d in rtm.mismatches(m)) and m.run(2000, 500)[0] >= 1.995
    pe = {"genref": "global.PE"}
    design = lambda: {"top": "global.app", "namespaces": {"global": {"modules": {"app": {
        "instances": {"in": {"genref": "global.IO"}, "pa": dict(pe), "pb": dict(pe), "mac1": dict(pe),
                      "mac2": dict(pe)},
        "connections": [["in.out", "pa.data0"], ["in.out", "mac1.data1"], ["in.out", "mac2.data1"],
                        ["pa.O0", "pb.data0"], ["pb.O0", "mac1.data0"], ["pb.O0", "mac2.data0"]]}}}}}
    assert rvb.balance(design(), pe_stages=0, margin=0, plan=plan)[0] == 8      # a chain per input
    d = design()
    assert rvb.balance(d, pe_stages=0, margin=0, plan=plan, share=True)[0] == 4  # one shared chain
    conns = [sorted(c) for c in d["namespaces"]["global"]["modules"]["app"]["connections"]]
    last = "rv_balance_" + hashlib.md5(b"in.out").hexdigest()[:8] + "_3.out"
    assert sorted([last, "mac1.data1"]) in conns and sorted([last, "mac2.data1"]) in conns
    assert sorted(["in.out", "pa.data0"]) in conns                               # unpadded sink stays


def test_replay_jobs_reach_the_tile_graphs(tmp_path):
    man = {"spec_config": {}, "mode": "static", "pond_spec": None}
    for argv, want in ((["--replay-jobs", "4"], "4"), ([], None)):
        args = cap.parse_args(["--out-dir", str(tmp_path)] + argv)
        env = cap.tile_env("Tile_PE", tmp_path, man, [("A", tmp_path)], "cfg", args)
        assert env.get("REPLAY_TILE_JOBS") == want


THESIS_MAN = {"spec_config": {"data_width": 16}, "pond_spec": None}


@pytest.mark.parametrize("man,argv,want", [
    (dict(THESIS_MAN, mode="static", thesis="static"), [], ("THESIS", "0.25")),
    (dict(THESIS_MAN, mode="rv", thesis="rv"), ["--i-delay-ns", "0.1"], ("0.1", "0.25")),
    (dict(THESIS_MAN, mode="rv"), [], (None, None)),            # stock fabric: the tiles' own
    (dict(THESIS_MAN, mode="rv"), ["--pt-i-delay-frac", "0.3"], (None, "0.3")),
])
def test_thesis_tiles_get_the_recipes_input_delays(tmp_path, man, argv, want):
    """The power tiles of a thesis bundle are constrained (and replayed) like the
    thesis tile set: TILE_I_DELAY_NS / PT_I_DELAY_FRAC as the sweep_specs recipes."""
    args = cap.parse_args(["--out-dir", str(tmp_path)] + argv)
    args.clocks = None
    env = cap.tile_env("Tile_PE", tmp_path, man, [("A", tmp_path)], "cfg", args)
    if want[0] == "THESIS":   # the thesis recipes' value, wherever sweep_specs sets it
        want = (f"{cap.sweep_specs().THESIS_I_DELAY_NS:g}", want[1])
    assert (env.get("TILE_I_DELAY_NS"), env.get("PT_I_DELAY_FRAC")) == want


def test_thesis_delays_match_the_recipes():
    ss = cap.sweep_specs()
    flags = ss._THESIS_TILE_FLAGS
    assert float(flags[flags.index("--pt-i-delay-frac") + 1]) == cap.THESIS_PT_I_DELAY_FRAC


def test_clocks_from_gives_each_fabric_its_clock(tmp_path, capsys):
    table = tmp_path / "thesis_clocks.json"
    table.write_text(json.dumps({"static": {"16": 515}, "rv": {"16": 560}}))
    args = cap.parse_args(["--out-dir", str(tmp_path), "--clocks-from", str(table)])
    args.clocks, _ = cap.sweep_specs()._thesis_clock_table(args.clocks_from)
    periods = {}
    for mode in ("static", "rv"):
        man = dict(THESIS_MAN, mode=mode, thesis=mode)
        env = cap.tile_env("Tile_MemCore", tmp_path, man, [("A", tmp_path)], "cfg", args)
        periods[mode] = (env["CLOCK_PERIOD"], env["clock_period_PE"])
    assert periods == {"static": ("1.942", "1.942"), "rv": ("1.786", "1.786")}
    stock = dict(THESIS_MAN, mode="rv")                         # not thesis: --clock-mhz
    assert cap.tile_env("Tile_PE", tmp_path, stock, [("A", tmp_path)], "cfg", args)["CLOCK_PERIOD"] == "1.333"
    with pytest.raises(SystemExit):                             # no dw32 clock in the table
        cap.config_clock_mhz(dict(stock, thesis="rv", spec_config={"data_width": 32}), args)
