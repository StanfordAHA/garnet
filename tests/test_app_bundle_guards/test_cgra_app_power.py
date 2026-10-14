"""mflowgen/cgra_app_power.py (whole-CGRA power of app-bundle variants), its
graph hook common/app_variants.py and gen_app_bundle.py --cgra-tiles: the
parts that run without the build machine (env parsing, tile roles, report
parsing and the per-variant sums)."""
import importlib.util
import json
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
