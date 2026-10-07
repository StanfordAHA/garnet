#!/usr/bin/env python3
"""Sweep lake-spec points through a garnet mflowgen build.

Standalone: depends only on the Python standard library, on `mflowgen`
being on PATH, and on this garnet checkout. It does not import lake, aha,
or anything else from the wider toolchain.

For each spec point:
    1. Write spec_config.json (kwargs consumed by cgra/util_onyx.py).
    2. Create a per-config mflowgen workspace under --out-dir.
    3. Run `mflowgen run --design <graph>` there with LAKE_SPEC_CONFIG /
       LAKE_SPEC_MODE / DUAL_PORT / USE_NON_SPLIT_FIFOS exported, so
       construct.py + common/rtl/gen_rtl.sh forward the knobs to garnet.py.
    4. Drive `make` up to --stop-after (default: cadence-innovus-signoff).
    5. Copy PPA-ish outputs into artifacts/ and append a row to results.csv.

The spec JSON is read back inside the build by cgra/util_onyx.py, which
passes the whole dict to lake's build_spec(**spec) for the tile's
SpecMemoryController (so every build_spec kwarg -- ports, dual_port,
vec_capacity, ... -- shapes the RTL), and derives the tile's SRAM
mem_width = data_width * vec_width and mem_depth from storage_capacity.

Spec sets (--spec-set): `default` is the 6 curated DEFAULT_SPEC_POINTS;
`thesis` is every spec of the standalone thesis synthesis sweep (lake
ASPLOS_EXP/all_experiments_thesis_v2.sh) plus those 6. Each spec is built
once per runtime mode in --runtime-mode (static, rv, or both); RV configs
get an `_rv` name suffix and select build_spec_rv in garnet.

--pnr-set splits the stop target per config: the named configs build to
--stop-after (signoff by default), every other config stops at --synth-stop
(Genus synthesis). With the 12 PnR anchors (`full12` = the 6 static
`full` points + their RV twins) correlation.csv fits tile PnR area against
tile synth area and projects PnR area for the synth-only configs.

With --standalone-synth, each spec point is ALSO synthesized on its own
(lake's pd/thesis graph: the bare `lakespec` module from
tests/test_spec/thesis_sweep.py, no tile wrapper) under
<out-dir>/standalone_synth/<config>/, at the tile's clock period. After
any run, <out-dir>/correlation.csv lines up standalone synth -> tile synth
-> tile PnR area/slack per config.

Requires a garnet whose garnet.py accepts --lake-spec-config (i.e. the
modern_gf lineage). On a garnet without it, the rtl step fails in argparse.
--standalone-synth additionally needs the sibling lake checkout (--lake-dir)
with `lake` importable by this Python.

Examples:
    # List what would run, touch nothing
    ./mflowgen/sweep_specs.py --dry-run

    # Single smoke point, RTL only
    ./mflowgen/sweep_specs.py --rtl-only --only fw1_dw16_sc4096_sp_in1_out1

    # Full sweep through signoff, 8-way make
    ./mflowgen/sweep_specs.py --parallel-jobs 8

    # Same, and zip the results for moving to another machine when done
    ./mflowgen/sweep_specs.py --parallel-jobs 8 --zip

    # Zip the results of an earlier run (no build)
    ./mflowgen/sweep_specs.py --zip-only --out-dir /path/to/tile_memcore_pnr

    # Full set: tile PnR + standalone spec synth, then correlation.csv
    ./mflowgen/sweep_specs.py --preset full --standalone-synth --zip

    # Add standalone synth to an already-finished tile sweep
    ./mflowgen/sweep_specs.py --preset full --standalone-only --out-dir ...

    # Idle + active MemTile power on the synth netlist for the 6 default
    # specs, static + RV (without --stop-after the configs run PnR and the
    # signoff netlist is powered too; --pnr-set limits that to some configs)
    ./mflowgen/sweep_specs.py --preset full --runtime-mode static,rv \\
        --stop-after cadence-genus-synthesis --memtile-power

    # Whole thesis set in the tile, static + RV: synth for all, PnR for the
    # 12 anchors; correlation.csv + correlation_fit.csv project the rest
    ./mflowgen/sweep_specs.py --spec-set thesis --runtime-mode static,rv \\
        --pnr-set full12 --config-jobs 4 --pnr-jobs 2 --zip
"""

from pathlib import Path
import argparse
import concurrent.futures
import csv
import functools
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import socket
import sys
import threading
import time
import zipfile


# Directory holding this script == <garnet>/mflowgen. Everything path-related
# is derived from it so the script is relocatable across machines.
MFLOWGEN_DIR = Path(__file__).resolve().parent
GARNET_DIR = MFLOWGEN_DIR.parent

# --standalone-synth: lake's per-spec mflowgen graph, built under
# <out-dir>/STANDALONE_SUBDIR/<config>/ (a sibling tree, NOT inside the tile
# workspace, where `make clean-all` would wipe it) up to STANDALONE_TARGET.
STANDALONE_SUBDIR = "standalone_synth"
STANDALONE_TARGET = "cadence-genus-synthesis"
# Where the lake rtl step's python_command writes the spec RTL + testbench;
# the step copies <test_dir>/inputs/lakespec.sv etc. into its outputs.
STANDALONE_TEST_DIR = "TEST/lakespec"


# ---------------------------------------------------------------------------
# Curated spec list. Each entry is one build. The axes here are the ones that
# actually move MemCore area/timing: fetch width, sram capacity, port count,
# and single- vs dual-port. Extend with --extra-specs.
# ---------------------------------------------------------------------------
DEFAULT_SPEC_POINTS = [
    # baseline: 4-wide fetch, 8KB SRAM, 2 in / 2 out, single-port
    dict(storage_capacity=8192, data_width=16, vec_width=4,
         in_ports=2, out_ports=2),

    # narrow-fetch single-port point (fw=1, dw=16, 4KB, 1x1)
    dict(storage_capacity=4096, data_width=16, vec_width=1,
         in_ports=1, out_ports=1),

    # 2-wide fetch, small SRAM, 1x1
    dict(storage_capacity=2048, data_width=16, vec_width=2,
         in_ports=1, out_ports=1),

    # wide fetch, large SRAM, 4x4
    dict(storage_capacity=32768, data_width=16, vec_width=8,
         in_ports=4, out_ports=4),

    # dual-port, 2-wide, 4KB, 2x2
    dict(storage_capacity=4096, data_width=16, vec_width=2,
         dual_port=True, in_ports=2, out_ports=2),

    # dual-port, 4-wide, 8KB, 4x4
    dict(storage_capacity=8192, data_width=16, vec_width=4,
         dual_port=True, in_ports=4, out_ports=4),
]


# Named subsets of DEFAULT_SPEC_POINTS, selectable with --preset. Values are
# config names (as produced by _config_name / shown by --list). Keep these in
# sync if a spec point above is renamed -- _collect_configs validates that every
# name in the chosen preset actually resolves to a config.
PRESETS = {
    # A small, diverse regression set that spans the axes the flow cares about:
    #   - single vs multi controller  -> the `mode` case-analysis guard
    #   - single vs dual port          -> S1DB vs SDPB SRAM macro family
    #   - small vs large geometry      -> spec-aware macro at both ends
    "smoke4": [
        "fw1_dw16_sc4096_sp_in1_out1",       # single-controller (mode guard)
        "fw4_dw16_sc8192_sp_in2_out2_vc2",   # multi-controller (mode present)
        "fw8_dw16_sc32768_sp_in4_out4_vc2",  # wide/large single-port macro
        "fw2_dw16_sc4096_dp_in2_out2_vc2",   # dual-port (SDPB family)
    ],
    # Every DEFAULT_SPEC_POINT -- the complete regression set. Adds, over
    # smoke4: fw4 single-port (in2/out2) and fw2 fetch=2/sc2048 single-port
    # (the narrow geometry with no 2-column macro -> cols=1 fallback).
    "full": [
        "fw4_dw16_sc8192_sp_in2_out2_vc2",
        "fw1_dw16_sc4096_sp_in1_out1",
        "fw2_dw16_sc2048_sp_in1_out1_vc2",
        "fw8_dw16_sc32768_sp_in4_out4_vc2",
        "fw2_dw16_sc4096_dp_in2_out2_vc2",
        "fw4_dw16_sc8192_dp_in4_out4_vc2",
    ],
}
# RV twins of `full` (needs --runtime-mode rv or static,rv), and the 12
# synth-vs-PnR correlation anchors: the static `full` points plus their twins.
PRESETS["full_rv"] = [n + "_rv" for n in PRESETS["full"]]
PRESETS["full12"] = PRESETS["full"] + PRESETS["full_rv"]

# build_spec()/build_spec_rv() kwargs with their defaults (lake
# spec/spec_memory_controller.py). An omitted key means the default on both
# sides, so it doubles as the dedup key and the naming defaults.
SPEC_DEFAULTS = dict(storage_capacity=4096, data_width=16, vec_width=4, dims=6,
                     in_ports=2, out_ports=2, dual_port=False, vec_capacity=2,
                     max_extent=None, max_sequence_width=None)

# Config keys that drive the sweep, not the RTL. They are stripped before
# spec_config.json is written: util_onyx passes that file to
# build_spec(**spec), which would reject them.
SWEEP_ONLY_KEYS = ("runtime_mode",)
RUNTIME_MODES = ("static", "rv")

# --memtile-power: the two stimulus variants (common/memtile-power-test-gen)
# and the stop targets that leave a signoff netlist to power the PnR level on.
MEMTILE_POWER_VARIANTS = ("idle", "active")
SIGNOFF_OR_LATER = ("signoff", "genlibdb", "lib2db", "calibre", "pegasus")


def _thesis_spec_points():
    """Every spec of the standalone thesis synthesis sweep, as build_spec
    kwargs: a 1:1 mirror of lake's ASPLOS_EXP/all_experiments_thesis_v2.sh
    (create_mflowgen_experiments.py grids, frequency/build_dir dropped).

    aha's sweep_thesis_collateral.enumerate_thesis_configs() lists the same
    grids but folds the max_sequence_width points together (they share
    collateral). They do not share RTL -- it sizes the address generator's
    stride registers -- so they stay separate here.
    """
    pts = []
    # PORT_EXP
    for dw in (8, 16, 32):
        pts.append(dict(storage_capacity=8192, data_width=dw, vec_width=4,
                        in_ports=2, out_ports=2))
    for fw, vc, dw in [(fw, vc, dw) for fw in (2, 4, 8) for vc in (2, 4, 8)
                       for dw in (8, 16)]:
        pts.append(dict(storage_capacity=8192, data_width=dw, vec_width=fw,
                        vec_capacity=vc, in_ports=2, out_ports=2))
    for fw, vc in [(fw, vc) for fw in (2, 4) for vc in (2, 4, 8)]:
        pts.append(dict(storage_capacity=8192, data_width=32, vec_width=fw,
                        vec_capacity=vc, in_ports=2, out_ports=2))
    for vc in (2, 4, 8):
        pts.append(dict(storage_capacity=8192, data_width=64, vec_width=2,
                        vec_capacity=vc, in_ports=2, out_ports=2))
    # ITERATION_DOMAIN_EXP: dims x max_extent
    for dims in range(1, 7):
        for me in (64, 256, 1024, 4096):
            pts.append(dict(storage_capacity=8192, data_width=16, vec_width=1,
                            dims=dims, max_extent=me, in_ports=2, out_ports=2))
    # AFFINE_PATTERN_GENERATOR_EXP: dims x max_sequence_width
    for dims in range(1, 7):
        for msw in (64, 256, 1024, 4096, 16384):
            pts.append(dict(storage_capacity=8192, data_width=16, vec_width=1,
                            dims=dims, max_sequence_width=msw,
                            in_ports=2, out_ports=2))
    # MEMORY_EXP: (fetch width, dual port, ports, capacities)
    for fw, dp, ports, caps in (
            (1, True, 1, (1024, 2048, 4096, 8192, 16384)),
            (2, True, 2, (1024, 2048, 4096, 8192, 16384)),
            (4, True, 4, (1024, 2048, 4096, 8192)),
            (2, False, 1, (2048, 4096, 8192, 16384, 32768)),
            (4, False, 2, (4096, 8192, 16384, 32768)),
            (8, False, 4, (8192, 16384, 32768))):
        for sc in caps:
            pt = dict(storage_capacity=sc, data_width=16, vec_width=fw,
                      in_ports=ports, out_ports=ports)
            if dp:
                pt["dual_port"] = True
            pts.append(pt)
    return pts


# --spec-set choices. `thesis` keeps the curated 6 (first, so their dicts and
# names win the dedup) so the `full`/`full12` PnR anchors are always in it.
SPEC_SETS = {
    "default": DEFAULT_SPEC_POINTS,
    "thesis": DEFAULT_SPEC_POINTS + _thesis_spec_points(),
}


def build_argparser():
    p = argparse.ArgumentParser(
        prog="sweep_specs.py",
        description="Sweep lake specs through a garnet mflowgen build.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Examples:")[-1],
    )
    p.add_argument("--out-dir", default="sweep_out/tile_memcore_pnr",
                   help="Sweep output dir, relative to cwd unless absolute "
                        "(default: %(default)s).")
    p.add_argument("--graph", dest="graph", default=str(MFLOWGEN_DIR / "Tile_MemCore"),
                   help="mflowgen graph directory. Tile_MemCore, tile_array "
                        "and full_chip all forward the lake-spec knobs down "
                        "to the memory-core RTL step (default: %(default)s).")
    p.add_argument("--runtime-mode", default="static", metavar="MODES",
                   help="Comma-separated lake runtime modes -> --lake-spec-mode: "
                        "static, rv, or static,rv to build every spec in both. "
                        "RV configs are named <config>_rv; specs build_spec_rv "
                        "rejects (vec_width>1 with vec_capacity>2) are skipped "
                        "for rv. A spec dict may pin its own 'runtime_mode' "
                        "(--extra-specs). Default: %(default)s.")
    p.add_argument("--spec-set", choices=sorted(SPEC_SETS), default="default",
                   help="Built-in spec list: 'default' = the 6 curated "
                        "DEFAULT_SPEC_POINTS; 'thesis' = every spec of the "
                        "standalone thesis synthesis sweep (lake "
                        "all_experiments_thesis_v2.sh) plus those 6. "
                        "Default: %(default)s.")
    p.add_argument("--pnr-set", default="", metavar="NAMES",
                   help="Comma-separated config names and/or preset names "
                        "(e.g. full12) that build to --stop-after; every other "
                        "selected config stops at --synth-stop. Unset: all "
                        "configs build to --stop-after. Names must exist in "
                        "--spec-set x --runtime-mode. They build in their own "
                        "--pnr-jobs pool.")
    p.add_argument("--synth-stop", default="cadence-genus-synthesis",
                   help="Stop target for configs NOT in --pnr-set "
                        "(default: %(default)s).")
    p.add_argument("--pnr-jobs", type=int, default=1, metavar="N",
                   help="With --pnr-set: build up to N --pnr-set configs "
                        "concurrently in their own pool, alongside the "
                        "--config-jobs pool that runs the synth-only configs, so "
                        "the long PnR builds neither take the synth slots nor "
                        "make the synths wait. Total load is config_jobs + "
                        "pnr_jobs builds. Ignored without --pnr-set "
                        "(default: %(default)s).")
    p.add_argument("--stop-after", default="cadence-innovus-signoff",
                   help="Step name or number to run up to via `make`. Must be a "
                        "real mflowgen step name (see `make list` in a "
                        "configured workspace), not the local variable name used "
                        "in construct.py. Common: rtl, cadence-genus-synthesis, "
                        "cadence-innovus-signoff (default: %(default)s).")
    p.add_argument("--rtl-only", action="store_true",
                   help="Shortcut for --stop-after rtl; fastest check that the "
                        "spec plumbing reaches garnet.py.")
    p.add_argument("--extra-specs",
                   help="JSON file: list of spec dicts to append to the "
                        "built-in list (or replace it, with --replace).")
    p.add_argument("--replace", action="store_true",
                   help="Drop DEFAULT_SPEC_POINTS; use only --extra-specs.")
    p.add_argument("--preset", choices=sorted(PRESETS), default=None,
                   help="Select a named subset of the built-in spec points. "
                        "'smoke4' is a diverse 4-build regression set (single/multi "
                        "controller, single/dual port, small/large geometry). "
                        "Composes with --only/--skip (all filters apply).")
    p.add_argument("--only", default="",
                   help="Comma-separated config names to include.")
    p.add_argument("--skip", default="",
                   help="Comma-separated config names to exclude.")
    p.add_argument("--parallel-jobs", type=int, default=0,
                   help="If >0, pass -j N to `make` inside each workspace "
                        "(parallelism WITHIN one build).")
    p.add_argument("--config-jobs", type=int, default=1, metavar="M",
                   help="Number of spec configs to build CONCURRENTLY (default 1 = "
                        "serial). Each config is an independent workspace, so they "
                        "run in parallel cleanly. Orthogonal to --parallel-jobs "
                        "(make -jN within a build); effective load is roughly "
                        "config_jobs x parallel_jobs. Mind RAM and Genus/Innovus "
                        "licenses -- e.g. 2 configs x -j6 is a common sweet spot. "
                        "With --pnr-set this is the synth-only pool; the "
                        "--pnr-set configs get --pnr-jobs. "
                        "Forced to 1 under --dry-run.")
    p.add_argument("--clean", default="",
                   help="Comma-separated step names/numbers to `make clean-<step>` "
                        "before building (after `mflowgen run`), forcing those steps "
                        "-- and everything downstream -- to rebuild from current "
                        "sources. Use when you edited a step's files (constraints, "
                        "construct.py, ...) but the workspace already exists: a plain "
                        "re-run reuses cached step dirs. mflowgen exposes a "
                        "clean-<name> alias per node. Example: "
                        "--clean constraints,cadence-genus-synthesis")
    p.add_argument("--clean-all", action="store_true",
                   help="`make clean-all` before building (full rebuild -- redoes the "
                        "expensive RTL step). Takes precedence over --clean.")
    p.add_argument("--fresh", action="store_true",
                   help="Completely delete each config's workspace dir (rm -rf) "
                        "before building -- a total wipe, unlike --clean-all which is "
                        "mflowgen's own clean and keeps Makefile/.mflowgen. Overrides "
                        "--clean/--clean-all and --skip-existing.")
    p.add_argument("--make", default="", metavar="TARGETS",
                   help="Passthrough: run `make <TARGETS>` in each selected config's "
                        "existing workspace and exit (no build). Forwards mflowgen's "
                        "own targets so you can drive the sweep's workspaces with the "
                        "verbs you already know: clean-all, clean-<N>, clean-<step>, "
                        "status, list, runtimes. Output goes straight to your "
                        "terminal. Space/comma-separated; unconfigured workspaces are "
                        "skipped. Examples: --make clean-all  |  --make status")
    p.add_argument("--non-split-fifos", dest="non_split_fifos",
                   action="store_true", default=True,
                   help="Build with --use-non-split-fifos (default).")
    p.add_argument("--no-non-split-fifos", dest="non_split_fifos",
                   action="store_false",
                   help="Build without --use-non-split-fifos.")
    p.add_argument("--use-sim-sram", action="store_true",
                   help="Build with behavioral (simulatable) SRAM instead of a "
                        "hardened macro. Needed for spec geometries with no "
                        "matching physical SRAM macro in the tech map.")
    # ---- App-driven power. Both paths are "round-trips" (the spec config is
    # sent up for app compilation either way); they differ in SCOPE:
    #   --cgra-power : app runs on the whole CGRA fabric -> tile power in fabric
    #                  context (container + Cadence/ADK path).
    #   --per-tile   : each memtile is simulated in isolation on the app's exact
    #                  access pattern (clockwork round-trip; container-free,
    #                  self-checked against golden).
    # They compose: pass both for fabric + isolated power side by side. ----
    p.add_argument("--cgra-power", "--power", dest="cgra_power",
                   action="store_true",
                   help="After the build, run the CGRA-fabric app-driven "
                        "PRE-SYNTHESIS + POST-SYNTHESIS power flow for each "
                        "spec instead of stopping at signoff. Sets "
                        "RTL_POWER=True and SYNTH_POWER=True (adds the RTL + "
                        "post-synth power nodes; the construct disables "
                        "power-aware PnR when either is set) and makes the "
                        "'post-rtl-power' (RTL-sim activity on the signoff "
                        "netlist via the Genus namemap) and 'post-synth-power' "
                        "leaves, which pull synth + the 'application' sim "
                        "(default app conv_3_3, run on the full fabric) as "
                        "dependencies. Add --include-pnr-power for the "
                        "gate-level PnR leaf too. (--power is a back-compat "
                        "alias.) NOTE: needs docker + Cadence (Innovus/Xcelium) "
                        "+ PrimeTime, i.e. the build machine, not /aha. "
                        "KNOWN LIMITATION: the 'application' step still runs the "
                        "app on the DEFAULT MemCore in the stock container, so "
                        "for lake-spec configs the stimulus does not match the "
                        "spec tile and the power numbers are not meaningful yet.")
    p.add_argument("--per-tile", dest="per_tile", action="store_true",
                   help="After the build, run the PER-TILE clockwork round-trip "
                        "power flow: the app is compiled against the spec and "
                        "each memtile is simulated in isolation on the exact "
                        "read/write stream it sees, self-checked against golden, "
                        "then powered at synth level. Sets PER_TILE_POWER=True "
                        "(adds the round-trip power node) and makes the "
                        "'per-tile-power' leaf. Container-free (uses the lake "
                        "spec testbench + xrun), but the power step needs "
                        "PrimeTime. Composes with --cgra-power.")
    p.add_argument("--memtile-power", dest="memtile_power", action="store_true",
                   help="Also measure each spec MemTile's IDLE and ACTIVE (max "
                        "sustainable traffic) power: lake's standalone idle/active "
                        "power tests ported to the tile. Sets MEMTILE_POWER=True "
                        "(adds memtile-power-test-gen + per-level/variant sim and "
                        "ptpx nodes) and adds the memtile-power-synth-{idle,active} "
                        "leaves (Genus netlist) to every config, plus "
                        "memtile-power-pnr-{idle,active} (signoff netlist) for "
                        "configs that build through PnR. The normal stop target is "
                        "kept, so area results are unchanged. Writes "
                        "<out-dir>/memtile_power.csv. Needs xrun (or VCS) + "
                        "PrimeTime, and docker for the stimulus generator unless "
                        "the rtl step runs without a container.")
    p.add_argument("--include-pnr-power", dest="include_pnr_power",
                   action="store_true",
                   help="With --cgra-power, additionally make the 'post-pnr-power' "
                        "leaf (gate-level power on the post-signoff routed "
                        "netlist). The node is always in the graph; this is what "
                        "triggers building it. Also supersedes --stop-after. "
                        "Same build-machine requirements as --cgra-power.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print each config's workspace + commands, run nothing.")
    p.add_argument("--skip-existing", action="store_true",
                   help="Skip configs whose workspace already has done.flag.")
    p.add_argument("--list", action="store_true",
                   help="Print the selected config names and exit.")
    p.add_argument("--zip", action="store_true",
                   help="When the sweep finishes (pass or fail), zip the results "
                        "for moving between machines: results.csv plus, per "
                        "config, spec/collateral JSON, top-level logs, per-step "
                        "mflowgen-run.log, the PPA/power reports and the SRAM "
                        "macro datasheet (see ARTIFACT_GLOBS). Workspaces "
                        "themselves are not included.")
    p.add_argument("--zip-only", action="store_true",
                   help="Standalone: zip the results already in --out-dir from a "
                        "previous run and exit (no build). Archives every config "
                        "workspace found there, or only the selected ones if "
                        "--preset/--only/--skip is given.")
    p.add_argument("--zip-path", metavar="PATH",
                   help="Where to write the zip for --zip/--zip-only (default: "
                        "next to --out-dir, named <out-dir>_<host>_<timestamp>.zip).")
    # ---- Standalone spec synthesis (correlation baseline) ----
    p.add_argument("--standalone-synth", action="store_true",
                   help="Also synthesize each spec point STANDALONE -- the bare "
                        "lake `lakespec` module, no tile wrapper -- through lake's "
                        "pd/thesis mflowgen graph up to cadence-genus-synthesis, "
                        "in <out-dir>/standalone_synth/<config>/. Runs after the "
                        "config's tile build (pass or fail). Pair with the normal "
                        "tile build for the standalone-synth -> tile-synth -> "
                        "tile-PnR correlation in correlation.csv. --fresh, "
                        "--skip-existing and --clean-all apply to it too; --clean "
                        "<steps> does not (tile step names).")
    p.add_argument("--standalone-only", action="store_true",
                   help="Like --standalone-synth but skip the tile builds entirely "
                        "(e.g. to add the standalone baseline to a finished tile "
                        "sweep in the same --out-dir). With --make, targets the "
                        "standalone workspaces instead of the tile ones.")
    p.add_argument("--lake-dir", metavar="DIR",
                   default=os.environ.get("LAKE_PATH", str(GARNET_DIR.parent / "lake")),
                   help="Lake checkout providing pd/thesis and "
                        "tests/test_spec/thesis_sweep.py for --standalone-synth "
                        "(default: $LAKE_PATH, else the garnet checkout's sibling "
                        "lake, as gen_rtl.sh does: %(default)s).")
    p.add_argument("--standalone-rtl", choices=["host", "container"],
                   default="host",
                   help="Where the standalone spec RTL is generated. 'host' "
                        "(default): thesis_sweep.py under this Python, with "
                        "--lake-dir put on PYTHONPATH automatically (lake's deps "
                        "-- kratos, magma, ... -- must be installed). 'container' "
                        "(opt-in, untested): in the aha docker image with lake at "
                        "origin/THESIS, like gen_rtl.sh does for the tile, so both "
                        "sides share one lake + kratos (see standalone_spec_rtl.sh).")
    p.add_argument("--standalone-clock-ps", type=float, default=None, metavar="PS",
                   help="Clock period for the standalone synth, in ps (the lake "
                        "graph's unit). Default: the tile's own clock_period read "
                        "from <--graph>/construct.py (ns, x1000) so both syntheses "
                        "target the same frequency.")
    p.add_argument("--correlate-only", action="store_true",
                   help="Rebuild <out-dir>/correlation.csv from existing "
                        "workspaces (tile + standalone) and exit; no build. "
                        "Selection works like --zip-only.")
    return p


def main(argv=None):
    args = build_argparser().parse_args(argv)

    if args.per_tile:
        # Parked: the round-trip graph node ('per-tile-power') is not wired into
        # Tile_MemCore yet, so fail up front instead of after mflowgen run.
        print("*** --per-tile is not implemented yet (the 'per-tile-power' node "
              "is not in the Tile_MemCore graph). For isolated per-spec power, "
              "run lake's ASPLOS_EXP/run_synth_pool.py instead.", file=sys.stderr)
        return 2

    if args.rtl_only and args.memtile_power:
        print("*** --memtile-power needs synthesis; drop --rtl-only.",
              file=sys.stderr)
        return 2
    if args.rtl_only:
        args.stop_after = "rtl"
    if args.standalone_only:
        args.standalone_synth = True
    args.modes = _parse_modes(args.runtime_mode)

    configs = _collect_configs(args)
    if not configs:
        print("No spec points selected; nothing to do.", flush=True)
        return 0
    args.pnr_names = _resolve_pnr_set(args, configs)
    if args.pnr_names is not None:
        # The PnR builds take hours; start them first so they aren't the tail.
        configs.sort(key=lambda c: _config_name(c) not in args.pnr_names)

    if args.list:
        for cfg in configs:
            print(_config_name(cfg))
        _print_selection_summary(configs, args, file=sys.stderr)
        return 0

    if args.make:
        return _run_make_passthrough(configs, args)

    if args.zip_only or args.correlate_only:
        # Only narrow to the selection when the user actually made one; otherwise
        # cover every workspace in --out-dir (it may hold --extra-specs configs
        # from the earlier run that are not in today's default list).
        out_dir = Path(args.out_dir).resolve()
        selected = args.preset or args.only or args.skip
        names = {_config_name(c) for c in configs} if selected else None
        if not out_dir.is_dir():
            print(f"*** ERROR: no results dir: {out_dir}", file=sys.stderr,
                  flush=True)
            return 1
        if not args.dry_run:
            found = _discover_configs(out_dir, names)
            _write_correlation(out_dir, found)
            _write_memtile_power(out_dir, found)
        if args.correlate_only and not args.zip_only:
            return 0
        return 0 if _zip_results(out_dir, names, args) else 1

    _preflight(args)
    if args.standalone_synth:
        _preflight_standalone(args)

    out_dir = Path(args.out_dir).resolve()
    if out_dir == GARNET_DIR or GARNET_DIR in out_dir.parents:
        print(
            f"*** WARNING: --out-dir is inside the garnet checkout ({out_dir}).\n"
            "    gen_rtl copies the garnet tree into its docker container; the\n"
            "    default sweep_out/ name is excluded from that copy, but other\n"
            "    in-tree build output can still break it on absolute adk symlinks.\n"
            "    Prefer an --out-dir outside the garnet repo, e.g.\n"
            f"      {GARNET_DIR.parent / 'sweep_out' / 'tile_memcore_pnr'}",
            file=sys.stderr, flush=True)
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        _write_plan(out_dir, configs, args)
    results_csv = out_dir / "results.csv"

    print(f"garnet:   {GARNET_DIR}", flush=True)
    print(f"graph:    {args.graph}", flush=True)
    print(f"out_dir:  {out_dir}", flush=True)
    if args.standalone_synth:
        print(f"lake:     {Path(args.lake_dir).resolve()}  (standalone synth @ "
              f"{args.standalone_clock_ps:g} ps, RTL on {args.standalone_rtl}"
              f"{', tile builds skipped' if args.standalone_only else ''})",
              flush=True)
    _print_selection_summary(configs, args)

    rows = []
    failures = 0
    total = len(configs)
    n_jobs = 1 if args.dry_run else max(1, args.config_jobs)
    results_lock = threading.Lock()

    def record(row):
        nonlocal failures
        if row is None:
            return
        with results_lock:
            if "FAIL" in (row["status"], row["standalone_status"]):
                failures += 1
            rows.append(row)
            _write_results(results_csv, rows)

    # One pool, or with --pnr-set two concurrent ones: the --pnr-set configs
    # (hours of PnR each) get their own --pnr-jobs slots so they neither
    # occupy the synth slots nor hold back the synth-only configs.
    numbered = list(enumerate(configs, start=1))
    if args.pnr_names is None or args.dry_run:
        pools = [("", numbered, n_jobs)]
    else:
        pools = [("PnR", [(i, c) for i, c in numbered
                          if _config_name(c) in args.pnr_names],
                  max(1, args.pnr_jobs)),
                 ("synth-only", [(i, c) for i, c in numbered
                                 if _config_name(c) not in args.pnr_names],
                  n_jobs)]
        pools = [p for p in pools if p[1]]

    if len(pools) == 1 and pools[0][2] == 1:
        for i, cfg in pools[0][1]:
            record(_process_config(i, total, cfg, out_dir, args))
    else:
        print("Running up to " + " + ".join(
            f"{w} {label + ' ' if label else ''}config(s)" for label, _, w in pools)
            + " concurrently.", flush=True)
        executors = [concurrent.futures.ThreadPoolExecutor(max_workers=w)
                     for _, _, w in pools]
        try:
            futs = [ex.submit(_process_config, i, total, cfg, out_dir, args)
                    for ex, (_, group, _) in zip(executors, pools)
                    for i, cfg in group]
            for fut in concurrent.futures.as_completed(futs):
                record(fut.result())
        finally:
            for ex in executors:
                ex.shutdown(wait=True)

    if args.dry_run:
        if args.zip:
            print(f"DRY-RUN zip: {_default_zip_path(out_dir, args)}", flush=True)
        print("\nDry run: nothing executed.", flush=True)
        return 0

    print(f"\nDone: {len(rows) - failures} ok, {failures} failed. "
          f"Results: {results_csv}", flush=True)
    # Every workspace in out_dir, not just this run's configs, so a partial
    # re-run (--only, --standalone-only) doesn't drop rows for the others.
    found = _discover_configs(out_dir, None)
    _write_correlation(out_dir, found)
    _write_memtile_power(out_dir, found)
    zip_ok = True
    if args.zip:
        zip_ok = _zip_results(out_dir, {_config_name(c) for c in configs}, args)
    return 1 if failures or not zip_ok else 0


def _tile_clock_ps(graph):
    """The tile graph's clock_period (ns, per Tile_MemCore's `set_units -time
    ns` constraints) as ps, or None if construct.py doesn't spell it out."""
    try:
        text = (Path(graph) / "construct.py").read_text()
    except OSError:
        return None
    m = re.search(r"['\"]clock_period['\"]\s*:\s*([0-9.]+)", text)
    if not m:
        return None
    ps = round(float(m.group(1)) * 1000, 3)
    return int(ps) if ps.is_integer() else ps


def _preflight_standalone(args):
    """Resolve the standalone clock and check the lake side exists."""
    lake = Path(args.lake_dir).resolve()
    for rel in ("pd/thesis/.mflowgen.yml", "tests/test_spec/thesis_sweep.py"):
        if not (lake / rel).is_file():
            raise SystemExit(
                f"*** ERROR: --standalone-synth needs {lake / rel}\n"
                "    Point --lake-dir (or $LAKE_PATH) at a lake THESIS checkout.")

    if args.standalone_clock_ps is None:
        args.standalone_clock_ps = _tile_clock_ps(args.graph)
        if args.standalone_clock_ps is None:
            raise SystemExit(
                f"*** ERROR: no 'clock_period' in {args.graph}/construct.py to "
                "match; pass --standalone-clock-ps explicitly.")

    if args.standalone_rtl == "container":
        if shutil.which("docker") is None:
            raise SystemExit("*** ERROR: --standalone-rtl container needs "
                             "`docker` on PATH (or use --standalone-rtl host).")
        return

    # Host mode: thesis_sweep.py runs under this interpreter against --lake-dir
    # (put first on PYTHONPATH by _standalone_env), so only lake's third-party
    # deps (kratos, magma, fault, ...) must be installed. Show the real
    # ImportError rather than guessing which one is missing.
    proc = subprocess.run([sys.executable, "-c", "import lake.spec.spec"],
                          env=_standalone_env(args), stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        tail = "\n".join("      " + l for l in proc.stdout.strip().splitlines()[-4:])
        raise SystemExit(
            f"*** ERROR: lake's RTL generator can't import under {sys.executable}:\n"
            f"{tail}\n"
            "    Use --standalone-rtl container (runs it in the aha docker image, "
            "like gen_rtl.sh),\n    or install lake's deps here: "
            f"pip install -e {lake}")


def _standalone_env(args):
    """Env for the standalone mflowgen run/make. The lake graph's construct
    imports lake.top.tech_maps (pure Python, no deps), so --lake-dir on
    PYTHONPATH is all the host needs for it -- no pip install. LAKE_PATH tells
    standalone_spec_rtl.sh which checkout to copy into the container."""
    lake = str(Path(args.lake_dir).resolve())
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in (lake, env.get("PYTHONPATH", "")) if p)
    env["LAKE_PATH"] = lake
    return env


def _preflight(args):
    """Fail early and legibly rather than deep inside a build."""
    graph = Path(args.graph)
    if not (graph / "construct.py").is_file():
        raise SystemExit(f"*** ERROR: no construct.py under --graph {graph}")

    if not args.dry_run and shutil.which("mflowgen") is None:
        raise SystemExit(
            "*** ERROR: `mflowgen` not found on PATH.\n"
            "    Install it and source its setup, e.g.:\n"
            "      git clone https://github.com/mflowgen/mflowgen\n"
            "      pip install -e mflowgen")

    # The lake-spec flags only exist on the modern_gf lineage; warn rather
    # than hard-fail, since garnet.py may legitimately move.
    garnet_py = GARNET_DIR / "garnet.py"
    try:
        if "--lake-spec-config" not in garnet_py.read_text():
            print("*** WARNING: garnet.py has no --lake-spec-config flag; the "
                  "rtl step will fail in argparse.\n"
                  "    Check out a garnet with lake-spec support "
                  "(e.g. the modern_gf branch).", file=sys.stderr, flush=True)
    except OSError:
        pass

    # A stale in-tree build dir (garnet/sweep_out from an earlier in-tree run)
    # breaks the rtl step: gen_rtl `docker cp`s the whole garnet checkout into
    # the build container, and an in-tree mflowgen workspace holds absolute adk
    # symlinks that docker cp rejects ("invalid symlink ..."). Fail fast with
    # the fix rather than deep inside the container -- but only when we are
    # building elsewhere (an intentional in-tree --out-dir is warned about
    # separately, in main()).
    stale = GARNET_DIR / "sweep_out"
    out_dir_resolved = Path(args.out_dir).resolve()
    stale_is_outdir = out_dir_resolved == stale or stale in out_dir_resolved.parents
    try:
        stale_nonempty = stale.is_dir() and any(stale.iterdir())
    except OSError:
        stale_nonempty = False
    if stale_nonempty and not stale_is_outdir:
        raise SystemExit(
            f"*** ERROR: stale in-tree build dir at {stale}\n"
            "    gen_rtl copies the garnet checkout into the build container, and\n"
            "    an in-tree mflowgen workspace holds absolute adk symlinks that\n"
            "    docker cp rejects ('invalid symlink ...'). Remove it and re-run:\n"
            f"      rm -rf {stale}")


# ---------------------------------------------------------------------------
# Config selection
# ---------------------------------------------------------------------------
def _parse_modes(text):
    modes = [m.strip() for m in text.split(",") if m.strip()]
    bad = [m for m in modes if m not in RUNTIME_MODES]
    if not modes or bad:
        raise SystemExit(f"*** ERROR: --runtime-mode takes a comma list of "
                         f"{'/'.join(RUNTIME_MODES)}, got '{text}'")
    return list(dict.fromkeys(modes))


def _mode(cfg):
    return cfg.get("runtime_mode", "static")


def _spec_key(spec):
    """Hardware identity of a spec: its build_spec kwargs, defaults filled."""
    return tuple(spec.get(k, v) for k, v in SPEC_DEFAULTS.items())


def _spec_kwargs(cfg):
    """The build_spec kwargs of a config, i.e. what goes in spec_config.json."""
    return {k: v for k, v in cfg.items() if k not in SWEEP_ONLY_KEYS}


def _unsupported_reason(spec, mode):
    """Why `mode` can't build this spec (None if it can). Mirrors the check
    at the top of lake's build_spec_rv, which raises."""
    if (mode == "rv" and spec.get("vec_width", 4) > 1
            and spec.get("vec_capacity", 2) > 2):
        return "build_spec_rv supports vec_capacity <= 2 for vec_width > 1"
    return None


def _collect_configs(args):
    specs = [] if args.replace else list(SPEC_SETS[args.spec_set])

    if args.extra_specs:
        with open(args.extra_specs) as f:
            payload = json.load(f)
        if not isinstance(payload, list):
            raise SystemExit(f"*** ERROR: --extra-specs must be a JSON list, "
                             f"got {type(payload).__name__}")
        specs.extend(payload)

    # One config per (spec, mode). A spec that pins runtime_mode keeps it.
    configs, seen_specs = [], set()
    args.skipped_rv = []
    for spec in specs:
        pinned = spec.get("runtime_mode")
        if pinned is not None and pinned not in RUNTIME_MODES:
            raise SystemExit(f"*** ERROR: spec {spec} has runtime_mode "
                             f"'{pinned}'; expected one of {RUNTIME_MODES}")
        for mode in ([pinned] if pinned else args.modes):
            key = (_spec_key(spec), mode)
            if key in seen_specs:
                continue  # same hardware listed twice (e.g. default + thesis)
            seen_specs.add(key)
            cfg = dict(spec, runtime_mode=mode)
            reason = _unsupported_reason(spec, mode)
            if reason:
                args.skipped_rv.append((_config_name(cfg), reason))
                continue
            configs.append(cfg)
    # Before --preset/--only/--skip narrow it: --pnr-set is checked against
    # this, so a narrowed re-run can keep the same --pnr-set.
    args.all_names = {_config_name(c) for c in configs}

    if args.preset:
        want = PRESETS[args.preset]
        available = {_config_name(c) for c in configs}
        missing = [n for n in want if n not in available]
        if missing:
            raise SystemExit(
                f"*** ERROR: preset '{args.preset}' names configs not in the spec "
                f"list: {', '.join(missing)}\n"
                f"    RV names need --runtime-mode rv (or static,rv); otherwise "
                f"the preset is stale -- update PRESETS in sweep_specs.py.")
        preset_names = set(want)
        configs = [c for c in configs if _config_name(c) in preset_names]

    if args.only:
        only = {s.strip() for s in args.only.split(",") if s.strip()}
        configs = [c for c in configs if _config_name(c) in only]
        unknown = only - {_config_name(c) for c in configs}
        if unknown:
            raise SystemExit(f"*** ERROR: --only names not in the spec list: "
                             f"{', '.join(sorted(unknown))}\n"
                             f"    Use --list to see available names.")
    if args.skip:
        skip = {s.strip() for s in args.skip.split(",") if s.strip()}
        configs = [c for c in configs if _config_name(c) not in skip]

    seen, unique = set(), []
    for c in configs:
        k = _config_name(c)
        if k in seen:
            continue
        seen.add(k)
        unique.append(c)
    return unique


def _config_name(cfg):
    """Stable name per config. Matches the naming used by the collateral
    sweeps in aha (so per-config dirs line up across both), plus `_msw<N>`
    for max_sequence_width (aha folds those; their RTL differs) and `_rv`
    for runtime mode rv. Static names are unchanged from earlier sweeps."""
    fw = cfg.get("vec_width", 4)
    dw = cfg.get("data_width", 16)
    sc = cfg.get("storage_capacity", 4096)
    dp = cfg.get("dual_port", False)
    inp = cfg.get("in_ports", 2)
    outp = cfg.get("out_ports", 2)
    vc = cfg.get("vec_capacity", 2)
    dims = cfg.get("dims", 6)
    me = cfg.get("max_extent")
    msw = cfg.get("max_sequence_width")

    parts = [f"fw{fw}_dw{dw}_sc{sc}"]
    parts.append("dp" if dp else "sp")
    parts.append(f"in{inp}_out{outp}")
    if fw > 1:
        parts.append(f"vc{vc}")
    if dims != 6:
        parts.append(f"dim{dims}")
    if me is not None:
        parts.append(f"me{me}")
    if msw is not None:
        parts.append(f"msw{msw}")
    if _mode(cfg) == "rv":
        parts.append("rv")
    return "_".join(parts)


def _resolve_pnr_set(args, configs):
    """--pnr-set -> set of config names (None when unset). Each item is a
    preset name or a config name, and must exist in the spec set x runtime
    modes (before --preset/--only/--skip, which may narrow the selection to
    only some or none of them)."""
    items = [s.strip() for s in args.pnr_set.split(",") if s.strip()]
    if not items:
        return None
    names = set()
    for item in items:
        names.update(PRESETS.get(item, [item]))
    missing = sorted(names - args.all_names)
    if missing:
        raise SystemExit(
            f"*** ERROR: --pnr-set names configs not in --spec-set "
            f"'{args.spec_set}' x --runtime-mode '{args.runtime_mode}': "
            f"{', '.join(missing)}\n    Use --list to see available names.")
    return names


def _stop_target(cfg, args):
    """make target for one config: --stop-after, or --synth-stop for configs
    outside --pnr-set. --rtl-only applies to all."""
    if args.rtl_only or args.pnr_names is None:
        return str(args.stop_after)
    if _config_name(cfg) in args.pnr_names:
        return str(args.stop_after)
    return str(args.synth_stop)


def _print_selection_summary(configs, args, file=None):
    file = file or sys.stdout
    by_mode = {m: sum(1 for c in configs if _mode(c) == m) for m in RUNTIME_MODES}
    modes = ", ".join(f"{n} {m}" for m, n in by_mode.items() if n)
    print(f"Sweeping {len(configs)} config(s) ({modes}) from spec set "
          f"'{args.spec_set}'.", file=file, flush=True)
    targets = {}
    for c in configs:
        t = " ".join(_all_targets(c, args))
        targets[t] = targets.get(t, 0) + 1
    for t, n in targets.items():
        print(f"  {n:4d} -> {t}", file=file, flush=True)
    reasons = {}
    for _, reason in args.skipped_rv:
        reasons[reason] = reasons.get(reason, 0) + 1
    for reason, n in reasons.items():
        print(f"  {n:4d} rv config(s) skipped: {reason}", file=file, flush=True)


# ---------------------------------------------------------------------------
# Per-config runner
# ---------------------------------------------------------------------------
PLAN_FILE = "sweep_plan.txt"


def _write_plan(out_dir, configs, args):
    """<out-dir>/sweep_plan.txt: every workspace this run will build (relative
    to out-dir, then its make targets), mirroring _process_config, under a
    `# pid= host= started=` header. watch_step.sh --summary reads it to list
    the configs not started yet and to tell whether this sweep is alive. Each
    run overwrites it."""
    host = socket.gethostname().split(".")[0]
    lines = [f"# pid={os.getpid()} host={host} "
             f"started={time.strftime('%Y-%m-%dT%H:%M:%S')}",
             "# " + shlex.join([sys.executable] + sys.argv)]
    for cfg in configs:
        name = _config_name(cfg)
        if not args.standalone_only:
            lines.append(f"{name} {' '.join(_all_targets(cfg, args))}")
        if args.standalone_synth and _mode(cfg) != "rv":
            lines.append(f"{STANDALONE_SUBDIR}/{name} standalone")
    (out_dir / PLAN_FILE).write_text("\n".join(lines) + "\n")


def _process_config(idx, total, cfg, out_dir, args):
    """Build one config (tile, then standalone if asked); return its results
    row (or None for a dry-run).

    Self-contained (catches its own build errors and returns a FAIL row) so it
    is safe to run either serially or concurrently via a thread pool.
    """
    name = _config_name(cfg)
    cfg_dir = out_dir / name
    print(f"\n[{idx}/{total}] {name}", flush=True)

    if args.standalone_only:
        row = None if args.dry_run else _row(name, cfg, cfg_dir, "SKIP",
                                             "standalone-only", 0.0, "")
    else:
        row = _process_tile(name, cfg, cfg_dir, args)

    if args.standalone_synth:
        if _mode(cfg) == "rv":
            # lake's standalone builder (thesis_sweep.py's
            # build_four_port_wide_fetch) forces opt_rv=False, so it can only
            # build the static spec. Don't file static RTL under an _rv name.
            print(f"        SKIP: {name} standalone (no standalone RV build)",
                  flush=True)
            sa = {"standalone_status": "SKIP",
                  "standalone_notes": "no standalone RV build"}
        else:
            sa = _process_standalone(name, cfg, out_dir / STANDALONE_SUBDIR / name,
                                     args)
        if row is not None:
            row.update(sa)
    return row


def _process_tile(name, cfg, cfg_dir, args):
    print(f"        workspace: {cfg_dir}", flush=True)

    # --fresh: completely remove the workspace before building (total wipe,
    # stronger than mflowgen's clean-all). Done before the skip-existing check
    # so it also overrides that.
    if args.fresh and cfg_dir.exists():
        if args.dry_run:
            print(f"        DRY-RUN: rm -rf {cfg_dir}", flush=True)
        else:
            print(f"        FRESH: rm -rf {cfg_dir}", flush=True)
            shutil.rmtree(cfg_dir)

    if not args.dry_run:
        cfg_dir.mkdir(parents=True, exist_ok=True)
    done_flag = cfg_dir / "done.flag"
    targets = " ".join(_all_targets(cfg, args))

    if args.skip_existing and _done_for(done_flag, targets):
        print(f"        SKIP: {name} (done.flag present)", flush=True)
        return _row(name, cfg, cfg_dir, "SKIP", "already_done", 0.0, targets)
    # done.flag = the latest build of this workspace succeeded. Drop an older
    # run's flag while rebuilding, so a failed re-run doesn't read as done
    # (watch_step.sh --summary).
    if not args.dry_run:
        done_flag.unlink(missing_ok=True)

    try:
        duration, notes = _run_one(cfg, cfg_dir, args)
        if args.dry_run:
            return None
        # A failed --memtile-power leaf leaves done.flag at the build targets,
        # so --skip-existing retries just the power leaves next time.
        done = targets if not notes else " ".join(_build_targets(cfg, args))
        done_flag.write_text(f"ok {done}\n")
        print(f"        PASS: {name} ({duration:.0f}s){' ' + notes if notes else ''}",
              flush=True)
        return _row(name, cfg, cfg_dir, "PASS", notes, duration, targets)
    except subprocess.CalledProcessError as e:
        print(f"        FAIL: {name} (exit {e.returncode})", flush=True)
        return _row(name, cfg, cfg_dir, "FAIL", f"exit_code={e.returncode}", 0.0,
                    targets)
    except Exception as e:  # noqa: BLE001 -- record and press on
        print(f"        FAIL: {name} ({str(e)[:120]})", flush=True)
        return _row(name, cfg, cfg_dir, "FAIL", str(e)[:200], 0.0, targets)


def _done_for(done_flag, targets):
    """done.flag reads `ok <targets>`. --skip-existing only skips a workspace
    built to the same targets, so moving a synth-only config into --pnr-set
    resumes it (make reuses the finished steps). A bare `ok` (written before
    targets were recorded) counts as done."""
    try:
        words = done_flag.read_text().split()
    except OSError:
        return False
    return words[:1] == ["ok"] and (len(words) == 1 or " ".join(words[1:]) == targets)


def _process_standalone(name, cfg, sa_dir, args):
    """Standalone counterpart of _process_tile; returns the row's
    standalone_* fields ({} for a dry-run)."""
    print(f"        standalone workspace: {sa_dir}", flush=True)

    if args.fresh and sa_dir.exists():
        if args.dry_run:
            print(f"        DRY-RUN: rm -rf {sa_dir}", flush=True)
        else:
            print(f"        FRESH: rm -rf {sa_dir}", flush=True)
            shutil.rmtree(sa_dir)

    done_flag = sa_dir / "done.flag"
    if args.skip_existing and done_flag.exists():
        print(f"        SKIP: {name} standalone (done.flag present)", flush=True)
        return {"standalone_status": "SKIP", "standalone_notes": "already_done"}
    if not args.dry_run:
        done_flag.unlink(missing_ok=True)   # see _process_tile

    def result(status, notes):
        print(f"        {status}: {name} standalone ({notes})", flush=True)
        return {"standalone_status": status, "standalone_notes": notes}

    try:
        duration = _run_standalone(cfg, sa_dir, args)
        if args.dry_run:
            return {}
        done_flag.write_text("ok\n")
        return result("PASS", f"{duration:.0f}s")
    except subprocess.CalledProcessError as e:
        return result("FAIL", f"exit_code={e.returncode}")
    except Exception as e:  # noqa: BLE001 -- record and press on
        return result("FAIL", str(e)[:200])


def _standalone_graph_kwargs(cfg, args):
    """--graph-kwargs for lake's pd/thesis graph, mirroring what lake's
    ASPLOS_EXP/create_mflowgen_experiments.py passes, for this spec point.

    The rtl step runs `python_command` (thesis_sweep.py, i.e. lake's
    build_four_port_wide_fetch -- the standalone twin of the build_spec the
    tile uses), either directly (--standalone-rtl host) or through
    standalone_spec_rtl.sh in the aha container, and copies the RTL from
    test_dir. Defaults match build_spec's so an omitted key means the same
    thing on both sides.
    """
    lake = Path(args.lake_dir).resolve()
    sc = cfg.get("storage_capacity", 4096)
    dw = cfg.get("data_width", 16)
    fw = cfg.get("vec_width", 4)
    dims = cfg.get("dims", 6)
    inp = cfg.get("in_ports", 2)
    outp = cfg.get("out_ports", 2)
    dp = bool(cfg.get("dual_port", False))
    vc = cfg.get("vec_capacity", 2)

    sweep_args = ["--storage_capacity", sc, "--data_width", dw,
                  "--fetch_width", fw, "--dimensionality", dims,
                  "--in_ports", inp, "--out_ports", outp,
                  "--vec_capacity", vc, "--clock_count_width", 64, "--physical"]
    if dp:
        sweep_args.append("--dual_port")
    for key in ("max_extent", "max_sequence_width"):
        if cfg.get(key) is not None:
            sweep_args += [f"--{key}", cfg[key]]

    if args.standalone_rtl == "container":
        cmd = ["bash", str(MFLOWGEN_DIR / "standalone_spec_rtl.sh"),
               STANDALONE_TEST_DIR, *sweep_args]
    else:
        cmd = [sys.executable, str(lake / "tests/test_spec/thesis_sweep.py"),
               *sweep_args, "--outdir", STANDALONE_TEST_DIR]

    kwargs = {
        "clock_period": args.standalone_clock_ps,
        "storage_capacity": sc,
        "data_width": dw,
        "fetch_width": fw,
        "dimensionality": dims,
        "in_ports": inp,
        "out_ports": outp,
        "dual_port": dp,
        "vec_capacity": vc,
        # Quoted so the rtl step's `$python_command` stays one exported string.
        "python_command": '"' + " ".join(str(c) for c in cmd) + '"',
        "test_dir": STANDALONE_TEST_DIR,
    }
    # Also as plain kwargs: lake's power-test-gen rebuilds the spec from them.
    for key in ("max_extent", "max_sequence_width"):
        if cfg.get(key) is not None:
            kwargs[key] = cfg[key]
    return kwargs


def _run_standalone(cfg, sa_dir, args):
    t0 = time.time()
    design = Path(args.lake_dir).resolve() / "pd" / "thesis"
    run_cmd = ["mflowgen", "run", "--design", str(design),
               "--graph-kwargs", str(_standalone_graph_kwargs(cfg, args))]
    make_cmd = ["make", STANDALONE_TARGET]
    if args.parallel_jobs > 0:
        make_cmd.insert(1, f"-j{args.parallel_jobs}")
    # Only clean-all carries over: --clean names tile-graph steps.
    clean_cmd = ["make", "clean-all"] if args.clean_all and not args.fresh else []

    if args.dry_run:
        print(f"        DRY-RUN cmd: {' '.join(run_cmd)}", flush=True)
        if clean_cmd:
            print(f"        DRY-RUN cmd: {' '.join(clean_cmd)}", flush=True)
        print(f"        DRY-RUN cmd: {' '.join(make_cmd)}", flush=True)
        return 0.0

    def write_spec():
        # Provenance, and what _discover_configs keys on (so even a workspace
        # whose `mflowgen run` failed gets correlated/zipped).
        _write_spec_files(cfg, sa_dir, STANDALONE_TARGET)

    sa_dir.mkdir(parents=True, exist_ok=True)
    write_spec()
    env = _standalone_env(args)
    _sh(run_cmd, cwd=sa_dir, env=env, log=sa_dir / "mflowgen_run.log")
    if clean_cmd:
        _sh(clean_cmd, cwd=sa_dir, env=env, log=sa_dir / "make_clean.log")
        write_spec()  # clean-all deletes loose files in the workspace

    _check_step_exists(STANDALONE_TARGET, sa_dir, env)
    _sh(make_cmd, cwd=sa_dir, env=env, log=sa_dir / "make.log")
    _collect_artifacts(sa_dir)
    return time.time() - t0


def _run_make_passthrough(configs, args):
    """Run `make <targets>` in each selected workspace and exit (no build).

    A thin passthrough to mflowgen's own make targets (clean-all, clean-<N>,
    clean-<step>, status, list, runtimes, ...) across every selected config, so
    regular mflowgen users can drive the sweep's workspaces with familiar verbs.
    Output is inherited (streamed to the terminal) rather than logged, so
    status/list/runtimes are readable. Workspaces without a Makefile (not yet
    configured) are skipped rather than erroring.
    """
    targets = args.make.replace(",", " ").split()
    out_dir = Path(args.out_dir).resolve()
    if args.standalone_only:
        out_dir = out_dir / STANDALONE_SUBDIR
    env = os.environ.copy()
    rc = 0
    for cfg in configs:
        name = _config_name(cfg)
        cfg_dir = out_dir / name
        print(f"\n[{name}] make {' '.join(targets)}   (cwd {cfg_dir})", flush=True)
        if not (cfg_dir / "Makefile").exists():
            print("        SKIP: no configured workspace (run a build first)",
                  flush=True)
            continue
        if args.dry_run:
            print(f"        DRY-RUN cmd: make {' '.join(targets)}", flush=True)
            continue
        proc = subprocess.run(["make", *targets], cwd=str(cfg_dir), env=env)
        if proc.returncode != 0:
            rc = proc.returncode
            print(f"        (make exited {proc.returncode})", flush=True)
    return rc


def _clean_targets(args):
    """Build the `make clean-...` command for --clean / --clean-all, or []."""
    if args.fresh:
        return []  # workspace was already rm -rf'd; nothing to mflowgen-clean
    if args.clean_all:
        return ["make", "clean-all"]
    steps = [s.strip() for s in args.clean.split(",") if s.strip()]
    if not steps:
        return []
    # mflowgen emits `clean-<name>` (alias) and `clean-<idx>` for every node.
    return ["make", *(f"clean-{s}" for s in steps)]


def _build_targets(cfg, args):
    """make targets for one tile build.

    Power leaves replace the plain stop target when requested.
      --cgra-power         -> fabric app power: pre-synth (RTL) + post-synth
      --include-pnr-power  -> (with --cgra-power) gate-level post-signoff (PnR)
      --per-tile           -> isolated per-memtile clockwork round-trip power
    All composable. Every leaf pulls its netlist + the app compile/sim as
    dependencies, so making them runs the whole chain. Otherwise the target
    is --stop-after, or --synth-stop for configs outside --pnr-set.

    --memtile-power leaves come on top: see _memtile_power_targets.
    """
    targets = []
    if args.cgra_power:
        targets += ["post-rtl-power", "post-synth-power"]
    if args.include_pnr_power:
        targets.append("post-pnr-power")
    if args.per_tile:
        targets.append("per-tile-power")
    return targets or [_stop_target(cfg, args)]


def _memtile_power_targets(cfg, args):
    """--memtile-power leaves, made AFTER the build targets in their own make
    (a power failure is a note on the row, not a failed config): synth level
    always, PnR level when the config builds through signoff (synth-only
    configs have no signoff netlist)."""
    if not getattr(args, "memtile_power", False):
        return []
    levels = ["synth"]
    if args.include_pnr_power or any(h in _stop_target(cfg, args) for h in SIGNOFF_OR_LATER):
        levels.append("pnr")
    return [f"memtile-power-{lvl}-{v}" for lvl in levels for v in MEMTILE_POWER_VARIANTS]


def _all_targets(cfg, args):
    return _build_targets(cfg, args) + _memtile_power_targets(cfg, args)


def _run_one(cfg, cfg_dir, args):
    t0 = time.time()

    spec_path = cfg_dir / "spec_config.json"
    env = os.environ.copy()
    env["LAKE_SPEC_CONFIG"] = str(spec_path)
    env["LAKE_SPEC_MODE"] = _mode(cfg)
    env["DUAL_PORT"] = "True" if cfg.get("dual_port", False) else "False"
    env["USE_NON_SPLIT_FIFOS"] = "True" if args.non_split_fifos else "False"
    env["USE_SIM_SRAM"] = "True" if args.use_sim_sram else "False"

    # The *_POWER env vars must be set BEFORE `mflowgen run` -- the construct
    # reads them at graph-materialization time to add the matching power nodes
    # (RTL/SYNTH also disable power-aware PnR). post-pnr-power is ALWAYS in the
    # graph, so its leaf needs no env toggle.
    if args.cgra_power:
        env["RTL_POWER"] = "True"
        env["SYNTH_POWER"] = "True"
    if args.per_tile:
        env["PER_TILE_POWER"] = "True"
    if args.memtile_power:
        env["MEMTILE_POWER"] = "True"
    build_targets = _build_targets(cfg, args)
    power_targets = _memtile_power_targets(cfg, args)

    make_cmd = ["make", *build_targets]
    power_cmd = ["make", *power_targets]
    if args.parallel_jobs > 0:
        make_cmd.insert(1, f"-j{args.parallel_jobs}")
        power_cmd.insert(1, f"-j{args.parallel_jobs}")

    # Steps to force-clean before building (see --clean / --clean-all). These
    # run after `mflowgen run` (so the Makefile + clean-<name> targets exist)
    # and before the build target.
    clean_cmd = _clean_targets(args)

    if args.dry_run:
        dry_env_keys = ["LAKE_SPEC_CONFIG", "LAKE_SPEC_MODE", "DUAL_PORT",
                        "USE_NON_SPLIT_FIFOS", "USE_SIM_SRAM"]
        if args.cgra_power:
            dry_env_keys += ["SYNTH_POWER", "RTL_POWER"]
        if args.per_tile:
            dry_env_keys += ["PER_TILE_POWER"]
        if args.memtile_power:
            dry_env_keys += ["MEMTILE_POWER"]
        for k in dry_env_keys:
            print(f"        DRY-RUN env: {k}={env[k]}", flush=True)
        print(f"        DRY-RUN cmd: mflowgen run --design {args.graph}",
              flush=True)
        if clean_cmd:
            print(f"        DRY-RUN cmd: {' '.join(clean_cmd)}", flush=True)
        print(f"        DRY-RUN cmd: {' '.join(make_cmd)}", flush=True)
        if power_targets:
            print(f"        DRY-RUN cmd: {' '.join(power_cmd)}", flush=True)
        return 0.0, ""

    _sh(["mflowgen", "run", "--design", str(args.graph)],
        cwd=cfg_dir, env=env, log=cfg_dir / "mflowgen_run.log")
    if clean_cmd:
        _sh(clean_cmd, cwd=cfg_dir, env=env, log=cfg_dir / "make_clean.log")

    # Write the spec AFTER any clean. `make clean-all` deletes every file in the
    # workspace except Makefile/.mflowgen* (find -maxdepth 1 ... -exec rm -rf),
    # so writing spec_config.json earlier would let clean-all erase it and make
    # the rtl step fail with "lake_spec_config file not found". mflowgen run only
    # needs the path (baked from LAKE_SPEC_CONFIG env), not the contents.
    _write_spec_files(cfg, cfg_dir, " ".join(build_targets + power_targets))

    for _t in build_targets + power_targets:
        _check_step_exists(_t, cfg_dir, env)
    _sh(make_cmd, cwd=cfg_dir, env=env, log=cfg_dir / "make.log")

    notes = ""
    if power_targets:
        try:
            _sh(power_cmd, cwd=cfg_dir, env=env, log=cfg_dir / "make_memtile_power.log")
        except subprocess.CalledProcessError as e:
            notes = f"memtile_power_failed(exit {e.returncode}, make_memtile_power.log)"

    _collect_artifacts(cfg_dir)
    return time.time() - t0, notes


def _write_spec_files(cfg, ws, targets):
    """spec_config.json = build_spec kwargs only (util_onyx passes it as
    **kwargs); sweep_meta.json = how the sweep built it (correlation reads
    runtime_mode/targets from it)."""
    with open(ws / "spec_config.json", "w") as f:
        json.dump(_spec_kwargs(cfg), f, indent=2, sort_keys=True)
    with open(ws / "sweep_meta.json", "w") as f:
        json.dump({"config_name": _config_name(cfg), "runtime_mode": _mode(cfg),
                   "targets": targets}, f, indent=2, sort_keys=True)


def _check_step_exists(step, cfg_dir, env):
    """Validate --stop-after against the configured graph's real targets.

    mflowgen derives make targets from step names, which are not the local
    variable names used in construct.py (e.g. the variable `signoff` is the
    step `cadence-innovus-signoff`). Catching a typo here beats discovering
    it as a bare "No rule to make target" after `mflowgen run` has already
    done its work. A numeric step id is always allowed.
    """
    if str(step).isdigit():
        return
    try:
        proc = subprocess.run(["make", "list"], cwd=str(cfg_dir), env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return  # Can't check; let make speak for itself.
    if proc.returncode != 0:
        return

    # `make list` prints one node per line as " -  23 : cadence-innovus-signoff"
    # (see mflowgen/backends/makefile_syntax.py: make_list). Generic targets
    # use "-- description" instead of ":". Collect both ids and names.
    names, targets = set(), set()
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        line = line.lstrip("-").strip()
        if " : " in line:
            num, name = line.split(" : ", 1)
            num, name = num.strip(), name.strip()
            targets.add(num)
            if name:
                targets.add(name)
                names.add(name)
        else:
            tok = line.split()[0] if line else ""
            if tok:
                targets.add(tok)
                names.add(tok)

    # If we parsed no step *names*, our parse of `make list` is wrong (or its
    # format changed). Stay quiet rather than block a legitimate build -- make
    # reports an unknown target in about a second anyway.
    if not names or step in targets:
        return

    near = sorted(n for n in names if step in n or n in step)
    hint = f"\n    Did you mean: {', '.join(near)}" if near else ""
    raise SystemExit(
        f"*** ERROR: '{step}' is not a step in this graph.{hint}\n"
        f"    Run `make list` in {cfg_dir} to see all targets.")


# The spec SRAM step (common/gen_sram_macro_spec) and the compiler datasheet
# its collect_datasheet.py links out of genviews-output/.
SRAM_STEP_GLOB = "*-gen_sram_macro_spec"
SRAM_DATASHEET_GLOB = SRAM_STEP_GLOB + "/outputs/sram_datasheet/*"

# Workspace-relative globs for the small subset of files that summarize PPA.
# Shared by _collect_artifacts (copy into artifacts/) and _zip_results.
ARTIFACT_GLOBS = [
    "*-cadence-innovus-signoff/outputs/*.lib",
    "*-cadence-innovus-signoff/outputs/*.lef",
    "*-cadence-innovus-signoff/outputs/*.gds",
    "*-cadence-innovus-signoff/reports/*.rpt",
    "*-cadence-innovus-signoff/reports/*.summary",
    # PT signoff: <design>.timing.{setup,hold}.rpt = top-100 PBA paths.
    "*-synopsys-pt-timing-signoff/reports/*.rpt",
    # Tile synth: <design>.timing.setup.top100{,.summary}.rpt = top-100
    # worst setup paths (Tile_MemCore custom-genus-scripts/generate-results.tcl).
    "*-cadence-genus-synthesis/reports/*.rpt",
    # Genus's write_snapshot -tag final: final_{area,gates,qor,time}.rpt --
    # the synth area/QoR numbers (_write_correlation parses these).
    "*-cadence-genus-synthesis/results_syn/final*.rpt",
    # SRAM macro min cycle time vs the clock target (check_sram_period.py).
    "*-gen_sram_macro_spec/reports/*.rpt",
    SRAM_DATASHEET_GLOB,   # the spec SRAM macro's datasheet
    # post-{rtl,synth,pnr}-power steps (common/tile-post-*-power): per-tile
    # power.hier copies land in outputs/reports/<tile_id>.hier.
    "*-post-*-power/outputs/reports/*",
    # --memtile-power: idle/active ptpx reports, the stimulus description
    # (tile, routes, programs, window) and each sim's self-check log.
    "*-memtile-power-*-idle/outputs/power.*",
    "*-memtile-power-*-active/outputs/power.*",
    "*-memtile-power-test-gen/outputs/power_tests.json",
    "*-memtile-power-sim-*/logs/sim.log",
]

# Extra per-workspace files that only go into the zip: provenance + logs, so a
# failed config can still be debugged on the other machine.
ZIP_EXTRA_GLOBS = [
    "*.json",               # spec_config.json, lake_collateral.json
    "*.log",                # mflowgen_run.log, make_clean.log, make.log
    "done.flag",
    "*/mflowgen-run.log",   # per-step log
    # Every file the SRAM compiler produced (+ its -help when no datasheet
    # matched), to fix the datasheet match from the zip alone.
    SRAM_STEP_GLOB + "/genviews_manifest.txt",
]

@functools.lru_cache(maxsize=None)
def _datasheet_finder():
    """collect_datasheet.find_datasheets, loaded from this checkout's node."""
    path = MFLOWGEN_DIR / "common" / "gen_sram_macro_spec" / "collect_datasheet.py"
    spec = importlib.util.spec_from_file_location("collect_datasheet", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.find_datasheets


def _old_sram_datasheets(cfg_dir):
    """Datasheets of SRAM steps that ran before collect_datasheet.py existed
    (no outputs/sram_datasheet/), found in their genviews-output/ with the
    same match rule, so a --zip-only of an older sweep still carries them."""
    return [f for step in cfg_dir.glob(SRAM_STEP_GLOB)
            if not (step / "outputs" / "sram_datasheet").is_dir()
            for f in _datasheet_finder()(step / "genviews-output")]


def _collect_artifacts(cfg_dir):
    """Copy the small subset of files that summarize PPA into artifacts/."""
    art = cfg_dir / "artifacts"
    art.mkdir(exist_ok=True)

    for pat in ARTIFACT_GLOBS:
        for src in cfg_dir.glob(pat):
            # artifacts/<NN-step>/<file>
            dst = art / src.relative_to(cfg_dir).parts[0] / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, dst)
            except OSError:
                pass


def _default_zip_path(out_dir, args):
    if args.zip_path:
        return Path(args.zip_path).resolve()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    host = socket.gethostname().split(".")[0]
    return out_dir.parent / f"{out_dir.name}_{host}_{stamp}.zip"


def _zip_results(out_dir, names, args):
    """Zip the sweep results under out_dir; return True on success.

    names: config names to include, or None for every workspace found in
    out_dir (see _discover_configs; covers both the tile workspace and its
    standalone_synth/ twin). Files are pulled straight from the workspaces
    (not from artifacts/), so configs that failed partway still contribute
    whatever reports/logs they got to. Paths inside the zip mirror the
    workspace layout under a single top-level dir named after the zip, so
    unpacking several archives side by side does not collide.
    """
    if not out_dir.is_dir():
        print(f"*** ERROR: no results dir to zip: {out_dir}", file=sys.stderr,
              flush=True)
        return False

    found = _discover_configs(out_dir, names)
    # sweep_plan.txt: the run's command line + its workspaces (provenance)
    files = sorted(out_dir.glob("*.csv")) + sorted(out_dir.glob(PLAN_FILE))
    sram_cfgs, no_datasheet = 0, []
    for name in found:
        for cfg_dir in (out_dir / name, out_dir / STANDALONE_SUBDIR / name):
            seen = set()
            for pat in ZIP_EXTRA_GLOBS + ARTIFACT_GLOBS:
                for src in cfg_dir.glob(pat):
                    if src.is_file() and src not in seen:
                        seen.add(src)
                        files.append(src)
            old = [f for f in _old_sram_datasheets(cfg_dir) if f not in seen]
            files += old
            if any(cfg_dir.glob(SRAM_STEP_GLOB)):
                sram_cfgs += 1
                if not old and not any(f.is_file() for f in
                                       cfg_dir.glob(SRAM_DATASHEET_GLOB)):
                    no_datasheet.append(name)

    zip_path = _default_zip_path(out_dir, args)
    root = zip_path.stem
    print(f"\nZipping {len(found)} config(s), {len(files)} file(s) from "
          f"{out_dir}\n        -> {zip_path}", flush=True)
    if sram_cfgs:
        print(f"        SRAM macro datasheet: {sram_cfgs - len(no_datasheet)}/"
              f"{sram_cfgs} config(s) with a gen_sram_macro_spec step",
              flush=True)
    if no_datasheet:
        print(f"*** WARNING: no SRAM datasheet for: {', '.join(no_datasheet)}"
              f"\n    (unfinished SRAM step, or the compiler wrote none: see "
              f"{SRAM_STEP_GLOB}/genviews_manifest.txt)", file=sys.stderr,
              flush=True)
    if not found:
        print("*** WARNING: no config workspaces found; zip will hold only "
              "results.csv (if any).", file=sys.stderr, flush=True)
    if args.dry_run:
        for f in files:
            print(f"        DRY-RUN add: {root}/{f.relative_to(out_dir)}",
                  flush=True)
        return True

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = zip_path.with_name(zip_path.name + ".partial")
    skipped = 0
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                try:
                    # write() follows symlinks, so mflowgen's outputs/ links
                    # are stored as their real contents.
                    zf.write(f, f"{root}/{f.relative_to(out_dir)}")
                except OSError as e:
                    skipped += 1
                    print(f"        skip {f}: {e}", file=sys.stderr, flush=True)
        tmp.replace(zip_path)
    except OSError as e:
        print(f"*** ERROR: writing {zip_path} failed: {e}", file=sys.stderr,
              flush=True)
        tmp.unlink(missing_ok=True)
        return False

    size_mb = zip_path.stat().st_size / 1e6
    note = f", {skipped} unreadable file(s) skipped" if skipped else ""
    print(f"Wrote {zip_path} ({size_mb:.1f} MB{note})", flush=True)
    return True


def _discover_configs(out_dir, names):
    """Config names with a workspace (tile or standalone) under out_dir, i.e.
    a spec_config.json in <out_dir>/<name>/ or <out_dir>/standalone_synth/
    <name>/. names: restrict to these (warning about any with no workspace),
    or None for all."""
    found = set()
    for parent in (out_dir, out_dir / STANDALONE_SUBDIR):
        if parent.is_dir():
            found |= {d.name for d in parent.iterdir()
                      if (d / "spec_config.json").is_file()}
    if names is not None:
        missing = sorted(set(names) - found)
        if missing:
            print(f"*** WARNING: no workspace in {out_dir} for: "
                  f"{', '.join(missing)}", file=sys.stderr, flush=True)
        found &= set(names)
    return sorted(found)


# ---------------------------------------------------------------------------
# Correlation: standalone synth -> tile synth -> tile PnR
# ---------------------------------------------------------------------------
# Report parsing is fail-soft: a missing/unparseable report is a blank cell,
# never an error, so correlation.csv can be regenerated mid-sweep. Areas are
# um^2 as the tools report them.
#
# SRAM is split out because the two flows need not pick the same macros: the
# standalone lake graph maps the whole word onto ONE GF_Tech_Map macro, while
# the tile's CoreCombiner prefers 2 half-width columns (lake CLAUDE.md 5.1).
# Compare the *_logic_area columns for the controller/wrapper cost.
SRAM_CELL_PREFIX = "IN12LP_"   # GF12 SRAM compiler macros (lake tech_maps.py)


def _first(ws, pattern):
    hits = sorted(ws.glob(pattern))
    return hits[0] if hits else None


def _read_lines(path):
    if path is None:
        return []
    try:
        return path.read_text(errors="replace").splitlines()
    except OSError:
        return []


def _nums(line):
    out = []
    for tok in line.split():
        try:
            out.append(float(tok))
        except ValueError:
            pass
    return out


def _top_row_nums(path):
    """Numeric fields of the top-design row of a hierarchical area report:
    the first non-blank line after the first ----- rule. Works for Genus
    final_area.rpt ([cells, cell_area, net_area, total_area]) and Innovus
    signoff.area.rpt ([insts, total, buf, inv, comb, flop, latch, cg, macro,
    physical]) regardless of whether a Module column is populated."""
    lines = _read_lines(path)
    for i, line in enumerate(lines):
        if re.match(r"^\s*-{10,}\s*$", line):
            for nxt in lines[i + 1:]:
                if nxt.strip():
                    return _nums(nxt)
            break
    return []


def _genus_sram(gates_rpt):
    """(total SRAM macro area, 'name x count; ...') from the per-cell table of
    Genus final_gates.rpt: the `<cell> <instances> <area> <library>` rows
    between the `Gate  Instances  Area  Library` header and its closing
    rule/`total` line, for SRAM_CELL_PREFIX cells.

    Only that table. report_gates follows it with per-Library and per-Type
    summaries, and a compiler SRAM's library is named after the macro
    (gen_srams.sh links IN12LP_MEM_genviews' <macro>_<corner>.lib as-is), so
    its Library row also starts with SRAM_CELL_PREFIX: scanning every line
    counted each macro twice (and drove *_logic_area negative)."""
    area, macros = 0.0, []
    in_table, rows_seen = False, False
    for line in _read_lines(gates_rpt):
        toks = line.split()
        if not in_table:
            in_table = (len(toks) >= 3 and toks[0] == "Gate"
                        and "Instances" in toks and "Area" in toks)
            continue
        if re.match(r"^\s*-{10,}\s*$", line):
            if rows_seen:
                break        # closing rule of the Gate table
            continue         # the rule under the header
        if not toks:
            continue
        if toks[0] == "total":
            break
        rows_seen = True
        if toks[0].startswith(SRAM_CELL_PREFIX):
            n = _nums(line)
            if len(n) >= 2:
                area += n[1]
                macros.append(f"{toks[0]} x{n[0]:g}")
    return (area if macros else None), "; ".join(macros)


def _genus_wns(qor_rpt):
    """Worst Critical Path Slack (ps) over the cost-group table of Genus
    final_qor.rpt, i.e. the rows between the two ----- rules under the
    `Cost / Critical / Violating` header, like `ideal_clock 495.3 0.0 0`.
    Rows without a numeric slack ('default  No paths') are skipped."""
    slacks, in_table, rules = [], False, 0
    for line in _read_lines(qor_rpt):
        if not in_table:
            in_table = "Critical" in line and "Violating" in line
            continue
        if re.match(r"^\s*-{10,}\s*$", line):
            rules += 1
            if rules == 2:
                break
            continue
        toks = line.split()
        if rules == 1 and len(toks) >= 2:
            try:
                slacks.append(float(toks[1]))
            except ValueError:
                pass
    return min(slacks) if slacks else None


def _pt_setup_wns(ws):
    """Worst setup slack from PrimeTime signoff (<design>.timing.setup.rpt),
    in library time units (ns for gf12)."""
    slacks = []
    for rpt in ws.glob("*-synopsys-pt-timing-signoff/reports/*.timing.setup.rpt"):
        for line in _read_lines(rpt):
            m = re.match(r"^\s*slack\s*\([^)]*\)\s+(-?\d+(?:\.\d+)?)", line)
            if m:
                slacks.append(float(m.group(1)))
    return min(slacks) if slacks else None


def _synth_metrics(ws, prefix):
    area_n = _top_row_nums(_first(ws, "*-cadence-genus-synthesis/results_syn/final_area.rpt"))
    cell = area_n[1] if len(area_n) >= 4 else None
    total = area_n[3] if len(area_n) >= 4 else None
    sram, macros = _genus_sram(_first(ws, "*-cadence-genus-synthesis/results_syn/final_gates.rpt"))
    logic = (cell - sram) if None not in (cell, sram) else None
    if logic is not None and logic < 0:
        # Cell area includes the macros, so this is a report-format surprise,
        # not a real number: leave it blank rather than feed it to the fit.
        print(f"*** WARNING: {ws.name} {prefix}: SRAM area {sram:.1f} > cell area "
              f"{cell:.1f}; leaving {prefix}_logic_area blank", file=sys.stderr,
              flush=True)
        logic = None
    return {
        f"{prefix}_cell_area": cell,
        f"{prefix}_total_area": total,
        f"{prefix}_sram_area": sram,
        f"{prefix}_logic_area": logic,
        f"{prefix}_wns_ps": _genus_wns(_first(ws, "*-cadence-genus-synthesis/results_syn/final_qor.rpt")),
        f"{prefix}_sram_macros": macros,
    }


def _pnr_metrics(ws):
    n = _top_row_nums(_first(ws, "*-cadence-innovus-signoff/reports/signoff.area.rpt"))
    total = n[1] if len(n) >= 2 else None
    macro = n[8] if len(n) >= 10 else None
    return {
        "tile_pnr_total_area": total,
        "tile_pnr_macro_area": macro,
        "tile_pnr_logic_area": (total - macro) if None not in (total, macro) else None,
        "tile_pnr_setup_wns_ns": _pt_setup_wns(ws),
    }


def _sweep_meta(ws, name):
    """runtime_mode/targets a workspace was built with (sweep_meta.json);
    workspaces from before it existed fall back to the name suffix."""
    try:
        meta = json.loads((ws / "sweep_meta.json").read_text())
    except (OSError, ValueError):
        meta = {}
    mode = meta.get("runtime_mode") or ("rv" if name.endswith("_rv") else "static")
    return {"runtime_mode": mode, "targets": meta.get("targets", "")}


# Tile synth -> tile PnR fits: (label, synth column, PnR column). Both sides
# are instance areas (Genus cell area vs Innovus signoff instance area). The
# die itself is sized from synth area at floorplan (fixed height, width =
# area/density), so it carries no extra information. `logic` drops the SRAM
# macros, which are identical in synth and PnR.
PNR_FITS = (
    ("total", "tile_synth_cell_area", "tile_pnr_total_area"),
    ("logic", "tile_synth_logic_area", "tile_pnr_logic_area"),
)
MIN_FIT_POINTS = 3


def _linfit(points):
    """Least-squares y = a + b*x over [(x, y)]; None if degenerate."""
    n = len(points)
    if n < MIN_FIT_POINTS:
        return None
    mx = sum(x for x, _ in points) / n
    my = sum(y for _, y in points) / n
    sxx = sum((x - mx) ** 2 for x, _ in points)
    syy = sum((y - my) ** 2 for _, y in points)
    sxy = sum((x - mx) * (y - my) for x, y in points)
    if sxx == 0:
        return None
    b = sxy / sxx
    a = my - b * mx
    errs = [abs(y - (a + b * x)) / y * 100 for x, y in points if y]
    return {
        "n": n, "slope": b, "intercept": a,
        "r2": (sxy * sxy / (sxx * syy)) if syy else 1.0,
        "mean_abs_pct_err": sum(errs) / len(errs) if errs else None,
        "max_abs_pct_err": max(errs) if errs else None,
        "x_min": min(x for x, _ in points), "x_max": max(x for x, _ in points),
    }


def _fit_and_project(rows):
    """Fit PnR area on synth area per group (all / static / rv) over rows with
    both, then add projected PnR area to every row with a synth area. A row
    uses its own mode's fit when that has MIN_FIT_POINTS, else the pooled
    one; proj_extrapolated flags synth areas outside the fitted range.
    Returns the fit-table rows."""
    groups = {"all": rows}
    for mode in RUNTIME_MODES:
        groups[mode] = [r for r in rows if r["runtime_mode"] == mode]
    table, fits = [], {}
    for label, xcol, ycol in PNR_FITS:
        for group, members in groups.items():
            pts = [(r[xcol], r[ycol]) for r in members
                   if isinstance(r[xcol], float) and isinstance(r[ycol], float)]
            fit = _linfit(pts)
            fits[(label, group)] = fit
            if fit:
                table.append({"metric": label, "group": group,
                              "synth_column": xcol, "pnr_column": ycol, **fit})
    for r in rows:
        for label, xcol, ycol in PNR_FITS:
            fit, used = fits.get((label, r["runtime_mode"])), r["runtime_mode"]
            if not fit:
                fit, used = fits.get((label, "all")), "all"
            x = r[xcol]
            if fit and isinstance(x, float):
                r[f"{ycol}_proj"] = fit["intercept"] + fit["slope"] * x
                r[f"{ycol}_proj_fit"] = used
                r[f"{ycol}_proj_extrapolated"] = (
                    "yes" if not fit["x_min"] <= x <= fit["x_max"] else "no")
            else:
                r[f"{ycol}_proj"] = None
                r[f"{ycol}_proj_fit"] = ""
                r[f"{ycol}_proj_extrapolated"] = ""
    return table


def _write_csv(path, rows):
    rows = [{k: (f"{v:.3f}" if isinstance(v, float) else v) for k, v in r.items()}
            for r in rows]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_correlation(out_dir, names):
    """Write <out_dir>/correlation.csv: per config, standalone synth vs tile
    synth vs tile PnR area/slack, pulled from whichever workspaces exist, plus
    PnR area projected from tile synth area; and correlation_fit.csv, the
    synth->PnR fits behind the projection (once >= MIN_FIT_POINTS configs
    have both)."""
    rows = []
    for name in names:
        row = {"config_name": name}
        row.update(_sweep_meta(out_dir / name, name))
        row.update(_synth_metrics(out_dir / STANDALONE_SUBDIR / name, "standalone_synth"))
        row.update(_synth_metrics(out_dir / name, "tile_synth"))
        row.update(_pnr_metrics(out_dir / name))
        rows.append(row)
    if not rows:
        return
    table = _fit_and_project(rows)
    path = out_dir / "correlation.csv"
    _write_csv(path, rows)
    print(f"Correlation: {path}", flush=True)
    if not table:
        return
    fit_path = out_dir / "correlation_fit.csv"
    _write_csv(fit_path, table)
    print(f"Synth->PnR fit: {fit_path}", flush=True)
    pct = lambda v: "n/a" if v is None else f"{v:.2f}%"  # noqa: E731
    for t in table:
        print(f"  {t['metric']:5s} {t['group']:6s} n={t['n']:<3d} "
              f"pnr = {t['slope']:.4f} * synth + {t['intercept']:.1f}   "
              f"R^2={t['r2']:.4f}   |err| mean {pct(t['mean_abs_pct_err'])} "
              f"max {pct(t['max_abs_pct_err'])}", flush=True)


def _memtile_power_metrics(ws):
    """Per (level, variant): PrimeTime's top-row [internal, switching,
    leakage, total] power of Tile_MemCore (the tool's report units, W unless
    the library sets others), plus the stimulus window from power_tests.json."""
    row = {}
    try:
        meta = json.loads(_first(ws, "*-memtile-power-test-gen/outputs/power_tests.json").read_text())
    except (AttributeError, OSError, ValueError):
        meta = {}
    for variant in MEMTILE_POWER_VARIANTS:
        row[f"{variant}_window_cycles"] = meta.get("variants", {}).get(variant, {}).get("window")
    # Pre-formatted: _write_csv's fixed 3 decimals would zero sub-mW powers.
    fmt = lambda v: None if v is None else f"{v:.6g}"  # noqa: E731
    for level in ("synth", "pnr"):
        total = {}
        for variant in MEMTILE_POWER_VARIANTS:
            n = _top_row_nums(_first(ws, f"*-memtile-power-{level}-{variant}/outputs/power.hier"))
            for i, part in enumerate(("internal", "switching", "leakage", "total")):
                row[f"{level}_{variant}_{part}_power"] = fmt(n[i]) if len(n) >= 4 else None
            total[variant] = n[3] if len(n) >= 4 else None
        idle, active = total["idle"], total["active"]
        row[f"{level}_active_over_idle"] = fmt(active / idle) if idle and active is not None else None
    return row


def _write_memtile_power(out_dir, names):
    """<out_dir>/memtile_power.csv: idle + active Tile_MemCore power per
    config (--memtile-power), synth and PnR netlists. Fail-soft like
    correlation.csv: blank cells for anything not built."""
    rows = []
    for name in names:
        ws = out_dir / name
        if not _first(ws, "*-memtile-power-test-gen"):
            continue
        row = {"config_name": name}
        row.update(_sweep_meta(ws, name))
        row.update(_memtile_power_metrics(ws))
        rows.append(row)
    if rows:
        path = out_dir / "memtile_power.csv"
        _write_csv(path, rows)
        print(f"MemTile idle/active power: {path}", flush=True)


def _sh(cmd, cwd, env, log):
    """Run a command tee-ing to a log file; raise on non-zero exit.

    stdin is /dev/null: a Genus/Innovus script error otherwise drops the tool
    to its interactive prompt, where it waits on the sweep's terminal forever
    (or is stopped by SIGTTIN when the sweep is backgrounded) and the sweep
    never returns. With no stdin the prompt reads EOF and the tool exits, so
    the step fails its postconditions and the config is recorded as FAIL.
    """
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    print(f"        $ {' '.join(cmd)}  (log: {log.name})", flush=True)
    with open(log, "w") as f:
        proc = subprocess.run(cmd, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
                              stdout=f, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        try:
            tail = log.read_text().splitlines()[-20:]
            print("        --- tail of log ---", flush=True)
            for line in tail:
                print(f"        {line}", flush=True)
        except OSError:
            pass
        raise subprocess.CalledProcessError(proc.returncode, cmd)


def _row(name, cfg, cfg_dir, status, notes, duration_s, targets):
    return {
        "config_name": name,
        "runtime_mode": _mode(cfg),
        "targets": targets,
        "storage_capacity": cfg.get("storage_capacity", 4096),
        "data_width": cfg.get("data_width", 16),
        "vec_width": cfg.get("vec_width", 4),
        "in_ports": cfg.get("in_ports", 2),
        "out_ports": cfg.get("out_ports", 2),
        "dual_port": cfg.get("dual_port", False),
        "vec_capacity": cfg.get("vec_capacity", 2),
        "dims": cfg.get("dims", 6),
        "max_extent": cfg.get("max_extent", ""),
        "max_sequence_width": cfg.get("max_sequence_width", ""),
        "status": status,
        "duration_s": f"{duration_s:.1f}",
        "workspace": str(cfg_dir),
        "notes": notes,
        # Filled in by _process_standalone under --standalone-synth.
        "standalone_status": "",
        "standalone_notes": "",
    }


def _write_results(csv_path, rows):
    if not rows:
        return
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    sys.exit(main())
