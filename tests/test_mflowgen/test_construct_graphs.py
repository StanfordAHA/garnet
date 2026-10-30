"""Every mflowgen design's construct() builds its Graph.

The construct scripts are otherwise only run on the build machine. Each design is built
in its own process (constructs edit sys.path and import modules named `construct` and
`common`), with a stub gf12 ADK and a stub `calibre` on PATH, since neither exists here.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MFLOWGEN = ROOT / "mflowgen"
DESIGNS = sorted(p.parent for p in list(MFLOWGEN.glob("*/construct.py")) + list(MFLOWGEN.glob("common/*/construct.py")))

BUILD = """
import contextlib, importlib.util, os, sys
d = sys.argv[1]
top = os.path.dirname(d)
if os.path.basename(top) == "common":
    top = os.path.dirname(top)
sys.path[:0] = [d, top]
os.chdir(d)
spec = importlib.util.spec_from_file_location("construct", os.path.join(d, "construct.py"))
m = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(sys.stderr):  # constructs print
    spec.loader.exec_module(m)
    g = m.construct()
print(len(g.all_nodes()))
"""


def stub_env(tmp_path, **extra):
    """Env for a construct() run here: a stub gf12 ADK and calibre on PATH."""
    mflowgen = pytest.importorskip("mflowgen")
    adk = tmp_path / "adks" / "gf12-adk"
    adk.mkdir(parents=True)
    (adk / "configure.yml").write_text("name: gf12-adk\n\noutputs:\n  - adk\n")
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    (stub_bin / "calibre").write_text("#!/bin/sh\nexit 0\n")
    (stub_bin / "calibre").chmod(0o755)
    env = dict(os.environ,
               MFLOWGEN_HOME=str(Path(mflowgen.__file__).resolve().parents[1]),
               MFLOWGEN_ADK_NAME="gf12-adk", MFLOWGEN_PATH=str(tmp_path / "adks"),
               PATH=f"{stub_bin}{os.pathsep}{os.environ.get('PATH', '')}",
               GARNET_HOME=str(ROOT),
               # common/tile-post-*-power read their parent tile's params from the env
               clock_period="1.0", design_name="Tile_PE")
    for k in ("LAKE_SPEC_CONFIG", "LAKE_SPEC_MODE", "DUAL_PORT"):
        env.pop(k, None)
    env.update(extra)
    return env


def build(design, env, *args, script=BUILD):
    res = subprocess.run([sys.executable, "-c", script, str(design), *args], env=env,
                         capture_output=True, text=True, timeout=600)
    assert res.returncode == 0, res.stderr[-5000:]
    return res.stdout.split()[-1]


@pytest.mark.parametrize("design", DESIGNS, ids=[str(d.relative_to(MFLOWGEN)) for d in DESIGNS])
def test_construct_builds_graph(design, tmp_path):
    assert int(build(design, stub_env(tmp_path))) > 1


@pytest.mark.parametrize("env,want", [
    ({}, "False"),
    ({"DUAL_PORT": "True"}, "False"),  # no spec: the default MemCore, as before
    ({"LAKE_SPEC_CONFIG": "spec.json", "LAKE_SPEC_MODE": "rv", "DUAL_PORT": "True"}, "True"),
    ({"LAKE_SPEC_CONFIG": "spec.json", "LAKE_SPEC_MODE": "rv", "DUAL_PORT": "False"}, "False"),
])
def test_tile_pe_rtl_dual_port(tmp_path, env, want):
    """An RV bundle's PE tile is built with the bundle's lake spec; a dual-port
    spec needs garnet --dual-port too, or lake's resolve_memports fails."""
    script = BUILD.replace("print(len(g.all_nodes()))", "print(g.get_step('rtl').get_param('dual_port'))")
    assert build(MFLOWGEN / "Tile_PE", stub_env(tmp_path, **env), script=script) == want


def test_tile_pe_pt_reads_the_whole_sdc(tmp_path):
    """PrimeTime's read_sdc stops at writeTimingCon's append_to_collection lines: the
    PE tile's signoff runs fix-pt-sdc.tcl after generate-results.tcl, and PT/genlibdb
    fail on "Errors reading SDC" instead of timing a truncated SDC."""
    script = BUILD.replace("print(len(g.all_nodes()))", "\n".join([
        "import json",
        "s = g.get_step('cadence-innovus-signoff')",
        "print(json.dumps([s.get_param('order'),",
        "                  g.get_step('synopsys-pt-timing-signoff').get_postconditions(),",
        "                  g.get_step('synopsys-ptpx-genlibdb').get_postconditions()]).replace(' ', ''))"]))
    order, pt_post, genlibdb_post = json.loads(build(MFLOWGEN / "Tile_PE", stub_env(tmp_path), script=script))
    assert order.index("fix-pt-sdc.tcl") > order.index("generate-results.tcl")
    for post in (pt_post, genlibdb_post):
        assert any("ErrorsreadingSDC" in p for p in post), post


def test_memtile_power_pnr_sims_get_the_signoff_sdf(tmp_path):
    """The PnR-level memtile power sims run the signoff netlist with its SDF
    (garnet/pnr-power-sim-no-sdf-race); the synth-level ones have none."""
    (tmp_path / "spec.json").write_text("{}")
    script = BUILD.replace("print(len(g.all_nodes()))", "\n".join([
        "import json",
        "e = {n: sorted([d[1], *s] for s, d in ((x.get_src(), x.get_dst()) for x in g.get_edges_i(n)))",
        "     for n in g.all_nodes() if n.startswith('memtile-power-sim-')}",
        "print(json.dumps(e).replace(' ', ''))"]))
    env = stub_env(tmp_path, MEMTILE_POWER="True", LAKE_SPEC_CONFIG=str(tmp_path / "spec.json"), LAKE_SPEC_MODE="rv")
    edges = json.loads(build(MFLOWGEN / "Tile_MemCore", env, script=script))
    assert len(edges) == 4
    for name, ins in edges.items():
        sdf = [e for e in ins if e[0] == "design.sdf"]
        if "-pnr-" in name:
            assert sdf == [["design.sdf", "cadence-innovus-signoff", "design.sdf"]], name
            assert ["design.v", "cadence-innovus-signoff", "design.vcs.v"] in ins, name
        else:
            assert sdf == [], name


@pytest.mark.parametrize("design,env,want", [
    ("Tile_PE", {}, False),
    ("Tile_PE", {"THESIS_FABRIC": "static"}, True),
    ("Tile_PE", {"THESIS_FABRIC": "rv", "LAKE_SPEC_CONFIG": "spec.json", "LAKE_SPEC_MODE": "rv"}, True),
    ("Tile_MemCore", {}, False),
    ("Tile_MemCore", {"LAKE_SPEC_CONFIG": "spec.json", "LAKE_SPEC_MODE": "static"}, True),
])
def test_fix_tap_gaps_after_the_well_taps(tmp_path, design, env, want):
    """A well tap one site from a fixed cell leaves a gap no GF12 filler fits, and
    route aborts with NRIG-76 (the static dw64 thesis PE tile, 2026-10-29): thesis
    PE tiles and lake-spec MemCores run fix-tap-gaps.tcl right after the taps go in;
    garnet's own tiles keep their graphs."""
    script = BUILD.replace("print(len(g.all_nodes()))", "\n".join([
        "import json",
        "print(json.dumps([g.get_step('cadence-innovus-init').get_param('order'),",
        "                  g.get_step('custom-init').all_outputs()]).replace(' ', ''))"]))
    order, outputs = json.loads(build(MFLOWGEN / design, stub_env(tmp_path, **env), script=script))
    assert ("fix-tap-gaps.tcl" in order) == want
    assert ("fix-tap-gaps.tcl" in outputs) == want
    if want:
        assert order.index("fix-tap-gaps.tcl") == order.index("add-endcaps-welltaps.tcl") + 1
        assert (MFLOWGEN / design / "custom-init" / "outputs" / "fix-tap-gaps.tcl").resolve() == \
            MFLOWGEN / "common" / "init-scripts" / "fix-tap-gaps.tcl"
