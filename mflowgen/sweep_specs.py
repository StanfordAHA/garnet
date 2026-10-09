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
    4. Drive `make` up to --stop-after (default: synopsys-pt-timing-signoff,
       i.e. PnR through signoff, then PrimeTime STA on the routed netlist).
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

    # The 16-bit thesis specs, hierarchy kept in synth (like lake's standalone
    # flow), idle/active power: synth all, PnR 12 of them; the synth->PnR model
    # is fit on 8 (dw16_fit8) and checked on the 4 held out (dw16_val4) ->
    # pnr_validation.csv
    ./mflowgen/sweep_specs.py --spec-set thesis --data-width 16 \\
        --runtime-mode static,rv --flatten-effort 0 --memtile-power \\
        --pnr-set dw16_pnr12 --validate-set dw16_val4 \\
        --config-jobs 4 --pnr-jobs 2 --zip

    # Whole-graph smoke test of one spec (lake build_spec defaults = the
    # default onyx MemCore geometry): standalone synth + its idle/active power,
    # tile PnR through PT signoff + tile idle/active power (synth + signoff
    # netlists), then the tile's signoff checks
    ./mflowgen/sweep_specs.py --spec-set thesis --only fw4_dw16_sc4096_sp_in2_out2_vc2 \\
        --flatten-effort 0 --memtile-power --standalone-synth \\
        --stop-after synopsys-pt-timing-signoff \\
        --also-make synopsys-ptpx-genlibdb,synopsys-dc-lib2db,drc,lvs,drcplus-pm --zip
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
# --memtile-power with --standalone-synth: lake's own idle/active power tests
# on the standalone synth netlist (pd/thesis power-test-gen -> VCS -> ptpx).
# The app-driven standalone power leaf (lake app-power-gen; graph kwarg
# app_bundle), made for a static config with an app bundle (--app-bundle-dir).
STANDALONE_APP_POWER_TARGET = "synopsys-ptpx-synth-app-power"
STANDALONE_POWER_TARGETS = ("synopsys-ptpx-synth-idle-power",
                            "synopsys-ptpx-synth-active-power")
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
# 16-bit thesis set (--spec-set thesis --data-width 16): 12 PnR builds, 8 to fit
# the synth->PnR model and 4 held out to check it (--validate-set dw16_val4).
# Fit: 4 specs x {static, rv} spanning the size range -- smallest (fw1 1x1),
# dual-port, fw4 2x2 sc8192 (the ports + SRAM of the big cluster below) and the
# largest (fw8 4x4 32 KB). Validate: 2 points from the fw1 sp 2x2 sc8192
# dims x max_extent / max_sequence_width cluster (108 of the 172 dw16 configs,
# none in full12), a dual-port 4x4 and a vec_capacity point.
PRESETS["dw16_fit8"] = [
    "fw1_dw16_sc4096_sp_in1_out1",
    "fw2_dw16_sc4096_dp_in2_out2_vc2",
    "fw4_dw16_sc8192_sp_in2_out2_vc2",
    "fw8_dw16_sc32768_sp_in4_out4_vc2",
]
PRESETS["dw16_fit8"] += [n + "_rv" for n in PRESETS["dw16_fit8"]]
PRESETS["dw16_val4"] = [
    "fw1_dw16_sc8192_sp_in2_out2_me4096",
    "fw1_dw16_sc8192_sp_in2_out2_dim4_msw1024_rv",
    "fw4_dw16_sc8192_dp_in4_out4_vc2_rv",
    "fw4_dw16_sc8192_sp_in2_out2_vc4",
]
PRESETS["dw16_pnr12"] = PRESETS["dw16_fit8"] + PRESETS["dw16_val4"]

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
    p.add_argument("--data-width", default="", metavar="WIDTHS",
                   help="Comma-separated data widths: keep only the specs with "
                        "one of these data_width values (e.g. 16). Applied before "
                        "--preset/--only/--skip, and --pnr-set/--validate-set "
                        "names must survive it. Default: all.")
    p.add_argument("--pnr-set", default="", metavar="NAMES",
                   help="Comma-separated config names and/or preset names "
                        "(e.g. full12) that build to --stop-after; every other "
                        "selected config stops at --synth-stop. Unset: all "
                        "configs build to --stop-after. Names must exist in "
                        "--spec-set x --runtime-mode. They build in their own "
                        "--pnr-jobs pool.")
    p.add_argument("--validate-set", default="", metavar="NAMES",
                   help="Comma-separated config/preset names (e.g. dw16_val4) "
                        "of PnR configs held OUT of the synth->PnR fits: their "
                        "PnR area and idle/active power are predicted from the "
                        "model fit on the other PnR configs and compared with "
                        "the real result in <out-dir>/pnr_validation.csv. Must be "
                        "in --pnr-set when that is given. Recorded per workspace "
                        "(sweep_meta.json pnr_role), so --correlate-only "
                        "reproduces the split without it; passing it there "
                        "overrides the recorded roles.")
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
    p.add_argument("--stop-after", default="synopsys-pt-timing-signoff",
                   help="Step name or number to run up to via `make`. Must be a "
                        "real mflowgen step name (see `make list` in a "
                        "configured workspace), not the local variable name used "
                        "in construct.py. Common: rtl, cadence-genus-synthesis, "
                        "cadence-innovus-signoff (PnR without PrimeTime timing), "
                        "synopsys-pt-timing-signoff (default: %(default)s; "
                        "signoff + PrimeTime STA, which correlation.csv's "
                        "tile_pnr_setup_wns_ns reads).")
    p.add_argument("--reuse-graph", action="store_true",
                   help="In a workspace that already has a Makefile, skip `mflowgen "
                        "run` and make the targets against the graph the workspace "
                        "was built with. Use to add a step to an existing sweep: "
                        "rerun it with --skip-existing --reuse-graph and only the "
                        "missing steps run, even if the current graph changed steps "
                        "the workspace already built (which would otherwise rebuild "
                        "them or trip the stale-step check). NOT for PT on a "
                        "workspace signed off before garnet 618adedd: its "
                        "design.pt.sdc lacks fix-pt-sdc.tcl, so PT reads a truncated "
                        "SDC (use --correlate-only for Innovus's signoff WNS "
                        "instead). Workspaces without a Makefile still get "
                        "`mflowgen run`.")
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
    p.add_argument("--clean-stale", action="store_true",
                   help="mflowgen does not rebuild a finished step when only its "
                        "parameters change (e.g. a new --flatten-effort on an "
                        "existing workspace), so after `mflowgen run` the sweep "
                        "compares each built step's parameters with the graph's "
                        "and FAILS the config if any differ. With this flag it "
                        "instead runs `make clean-<step>` for those steps (their "
                        "downstream steps rebuild too) and builds.")
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
    p.add_argument("--flatten-effort", type=int, choices=range(4), default=None,
                   metavar="N",
                   help="Genus flatten_effort for the tile synth (env FLATTEN, "
                        "read by Tile_MemCore/construct.py). 0 keeps the design "
                        "hierarchy (auto_ungroup none), like lake's standalone "
                        "pd/thesis synth, so area/power reports break down per "
                        "submodule; 1-3 let Genus ungroup (auto_ungroup both: the "
                        "Genus node only distinguishes 0 from non-zero). Default: "
                        "the graph's own value (3 for Tile_MemCore).")
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
                        "the rtl step runs without a container. With "
                        "--standalone-synth, the standalone build also makes "
                        "lake's own idle/active power leaves (synopsys-ptpx-synth-"
                        "{idle,active}-power, same programs + input streams) -> "
                        "standalone_* columns of memtile_power.csv.")
    p.add_argument("--also-make", default="", metavar="TARGETS",
                   help="Comma-separated extra tile-graph targets made after the "
                        "build (and --memtile-power) targets, e.g. "
                        "synopsys-ptpx-genlibdb,synopsys-dc-lib2db,drc,lvs. A name "
                        "that is not a step resolves to the one step ending in "
                        "-<name> (drc/lvs are mentor-calibre-* or cadence-pegasus-* "
                        "depending on `calibre` on PATH). A failure is a note on "
                        "the row, not a failed config.")
    p.add_argument("--include-pnr-power", dest="include_pnr_power",
                   action="store_true",
                   help="With --cgra-power, additionally make the 'post-pnr-power' "
                        "leaf (gate-level power on the post-signoff routed "
                        "netlist). The node is always in the graph; this is what "
                        "triggers building it. Also supersedes --stop-after. "
                        "Same build-machine requirements as --cgra-power.")
    p.add_argument("--app-bundle-dir", dest="app_bundle_dir", default=None,
                   help="Directory of app bundles recorded on the lake-spec CGRA "
                        "(one per config, at <dir>/<config name>/: run.vcd, "
                        "tiles_*.list, tile_ports.json, manifest.json; generated "
                        "in /aha, see mflowgen/CLAUDE.md 'App bundles'). A "
                        "config with a bundle replays that app run into its "
                        "power steps (APP_BUNDLE) instead of running the app on "
                        "the default MemCore in the stock container. Use with "
                        "--cgra-power / --include-pnr-power.")
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
    p.add_argument("--zip-slim", action="store_true",
                   help="With --zip/--zip-only: leave out the signoff layout and "
                        "library views (merged GDS, LEF, LIB), which are most of a "
                        "PnR config's size and which no report or CSV needs. Keeps "
                        "every report, log, manifest and CSV. Default zip name "
                        "gets a _slim suffix.")
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
    args.validate_names = _resolve_validate_set(args)
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
            _write_reports(out_dir, _discover_configs(out_dir, names), args)
        if args.correlate_only and not args.zip_only:
            return 0
        return 0 if _zip_results(out_dir, names, args) else 1

    _preflight(args)
    if args.standalone_synth:
        _preflight_standalone(args)
    # Recorded in every workspace's build_manifest.json.
    args.provenance = _sweep_provenance(args)

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
    _write_reports(out_dir, _discover_configs(out_dir, None), args)
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

    # --flatten-effort travels as env FLATTEN, which only some graphs read.
    if args.flatten_effort is not None:
        try:
            reads = "FLATTEN" in (graph / "construct.py").read_text()
        except OSError:
            reads = True
        if not reads:
            print(f"*** WARNING: {graph / 'construct.py'} does not read FLATTEN; "
                  "--flatten-effort has no effect on this graph.",
                  file=sys.stderr, flush=True)


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

    if args.data_width:
        try:
            widths = {int(w) for w in args.data_width.split(",") if w.strip()}
        except ValueError:
            raise SystemExit(f"*** ERROR: --data-width takes a comma list of "
                             f"integers, got '{args.data_width}'")
        specs = [s for s in specs
                 if s.get("data_width", SPEC_DEFAULTS["data_width"]) in widths]

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


def _resolve_names(args, text, flag):
    """A comma list of preset and/or config names -> set of config names
    (None when empty). Every name must exist in the spec set x runtime modes
    (x --data-width), before --preset/--only/--skip, which may narrow the
    selection to only some or none of them."""
    items = [s.strip() for s in text.split(",") if s.strip()]
    if not items:
        return None
    names = set()
    for item in items:
        names.update(PRESETS.get(item, [item]))
    missing = sorted(names - args.all_names)
    if missing:
        widths = f" x --data-width '{args.data_width}'" if args.data_width else ""
        raise SystemExit(
            f"*** ERROR: {flag} names configs not in --spec-set "
            f"'{args.spec_set}' x --runtime-mode '{args.runtime_mode}'{widths}: "
            f"{', '.join(missing)}\n    Use --list to see available names.")
    return names


def _resolve_pnr_set(args, configs):
    """--pnr-set -> set of config names (None when unset)."""
    return _resolve_names(args, args.pnr_set, "--pnr-set")


def _resolve_validate_set(args):
    """--validate-set -> set of config names (None when unset). They are
    validation points for the synth->PnR model, so they must build PnR."""
    names = _resolve_names(args, args.validate_set, "--validate-set")
    if names and args.pnr_names is not None:
        outside = sorted(names - args.pnr_names)
        if outside:
            raise SystemExit(
                f"*** ERROR: --validate-set configs must also be in --pnr-set "
                f"(they need PnR results): {', '.join(outside)}")
    return names


def _pnr_role(cfg, args):
    """Role in the synth->PnR model: 'validate' (PnR, held out of the fits),
    'fit' (PnR, fits them) or 'synth' (no PnR result)."""
    if _config_name(cfg) in (args.validate_names or ()):
        return "validate"
    if args.include_pnr_power or any(h in _stop_target(cfg, args)
                                     for h in SIGNOFF_OR_LATER):
        return "fit"
    return "synth"


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
    roles = {}
    for c in configs:
        role = _pnr_role(c, args)
        roles[role] = roles.get(role, 0) + 1
    if roles.get("validate"):
        print(f"  PnR model: fit on {roles.get('fit', 0)}, validated on "
              f"{roles['validate']} held-out config(s)", file=file, flush=True)
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
        changed = _changed_settings(cfg_dir, _build_settings(_tile_env(cfg, cfg_dir, args)))
        if not changed:
            print(f"        SKIP: {name} (done.flag present)", flush=True)
            return _row(name, cfg, cfg_dir, "SKIP", "already_done", 0.0, targets)
        print(f"        {name}: done.flag present but built with other settings "
              f"({changed}); rebuilding", flush=True)
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
        _finish_manifest(cfg_dir, "PASS", notes, duration)
        return _row(name, cfg, cfg_dir, "PASS", notes, duration, targets)
    except subprocess.CalledProcessError as e:
        print(f"        FAIL: {name} (exit {e.returncode})", flush=True)
        _finish_manifest(cfg_dir, "FAIL", f"exit_code={e.returncode}", None)
        return _row(name, cfg, cfg_dir, "FAIL", f"exit_code={e.returncode}", 0.0,
                    targets)
    except Exception as e:  # noqa: BLE001 -- record and press on
        print(f"        FAIL: {name} ({str(e)[:120]})", flush=True)
        _finish_manifest(cfg_dir, "FAIL", str(e), None)
        return _row(name, cfg, cfg_dir, "FAIL", str(e)[:200], 0.0, targets)


def _done_for(done_flag, targets, bare_ok=None):
    """done.flag reads `ok <targets>`. --skip-existing only skips a workspace
    built to the same targets, so moving a synth-only config into --pnr-set
    resumes it (make reuses the finished steps). A bare `ok` (written before
    targets were recorded) counts as done, or as `ok <bare_ok>` if given."""
    try:
        words = done_flag.read_text().split()
    except OSError:
        return False
    if words == ["ok"]:
        return bare_ok is None or bare_ok == targets
    return words[:1] == ["ok"] and " ".join(words[1:]) == targets


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
    targets = " ".join(_standalone_targets(cfg, args))
    if args.skip_existing and _done_for(done_flag, targets, bare_ok=STANDALONE_TARGET):
        print(f"        SKIP: {name} standalone (done.flag present)", flush=True)
        return {"standalone_status": "SKIP", "standalone_notes": "already_done"}
    if not args.dry_run:
        done_flag.unlink(missing_ok=True)   # see _process_tile

    def result(status, notes):
        print(f"        {status}: {name} standalone ({notes})", flush=True)
        _finish_manifest(sa_dir, status, notes,
                         duration if status == "PASS" else None)
        return {"standalone_status": status, "standalone_notes": notes}

    duration = None
    try:
        duration, notes = _run_standalone(cfg, sa_dir, args)
        if args.dry_run:
            return {}
        # As for the tile: a failed power leaf leaves done.flag at the synth
        # target, so --skip-existing retries just the power leaves.
        done_flag.write_text(f"ok {targets if not notes else STANDALONE_TARGET}\n")
        return result("PASS", " ".join(filter(None, [f"{duration:.0f}s", notes])))
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
    # The standalone lakespec is static: an app bundle replays into it only
    # from a static run (lake app-power-gen checks the spec too).
    bundle = _app_bundle(cfg, args)
    if bundle and _mode(cfg) == "static":
        kwargs["app_bundle"] = str(bundle)
    # Also as plain kwargs: lake's power-test-gen rebuilds the spec from them.
    for key in ("max_extent", "max_sequence_width"):
        if cfg.get(key) is not None:
            kwargs[key] = cfg[key]
    return kwargs


def _standalone_targets(cfg, args):
    """The standalone build's make targets: synth, plus lake's idle/active
    power leaves under --memtile-power, plus the app-driven leaf when the
    config has a static app bundle (--app-bundle-dir)."""
    power = list(STANDALONE_POWER_TARGETS) if args.memtile_power else []
    if "app_bundle" in _standalone_graph_kwargs(cfg, args):
        power.append(STANDALONE_APP_POWER_TARGET)
    return [STANDALONE_TARGET] + power


def _run_standalone(cfg, sa_dir, args):
    """Build one standalone workspace; returns (duration, notes)."""
    t0 = time.time()
    design = Path(args.lake_dir).resolve() / "pd" / "thesis"
    run_cmd = ["mflowgen", "run", "--design", str(design),
               "--graph-kwargs", str(_standalone_graph_kwargs(cfg, args))]
    make_cmd = ["make", STANDALONE_TARGET]
    power_targets = _standalone_targets(cfg, args)[1:]
    power_cmd = ["make", *power_targets]
    if args.parallel_jobs > 0:
        make_cmd.insert(1, f"-j{args.parallel_jobs}")
        power_cmd.insert(1, f"-j{args.parallel_jobs}")
    # Only clean-all carries over: --clean names tile-graph steps.
    clean_cmd = ["make", "clean-all"] if args.clean_all and not args.fresh else []

    if args.dry_run:
        print(f"        DRY-RUN cmd: {' '.join(run_cmd)}", flush=True)
        if clean_cmd:
            print(f"        DRY-RUN cmd: {' '.join(clean_cmd)}", flush=True)
        print(f"        DRY-RUN cmd: {' '.join(make_cmd)}", flush=True)
        if power_targets:
            print(f"        DRY-RUN cmd: {' '.join(power_cmd)}", flush=True)
        return 0.0, ""

    def write_spec():
        # Provenance, and what _discover_configs keys on (so even a workspace
        # whose `mflowgen run` failed gets correlated/zipped).
        _write_spec_files(cfg, sa_dir, " ".join(_standalone_targets(cfg, args)))

    sa_dir.mkdir(parents=True, exist_ok=True)
    write_spec()
    env = _standalone_env(args)
    _materialize_graph(sa_dir, run_cmd, env, clean_cmd,
                       args.reuse_graph and (sa_dir / "Makefile").is_file(), args)
    if clean_cmd:
        write_spec()  # clean-all deletes loose files in the workspace

    for target in [STANDALONE_TARGET] + power_targets:
        _check_step_exists(target, sa_dir, env)
    _write_manifest(sa_dir, cfg, args, "standalone",
                    settings={k: env[k] for k in ("PYTHONPATH", "LAKE_PATH") if k in env},
                    targets={"build": [STANDALONE_TARGET], "power": power_targets},
                    graph=str(design), graph_kwargs=_standalone_graph_kwargs(cfg, args))
    _sh(make_cmd, cwd=sa_dir, env=env, log=sa_dir / "make.log")
    notes = ""
    if power_targets:
        try:
            _sh(power_cmd, cwd=sa_dir, env=env, log=sa_dir / "make_power.log")
        except subprocess.CalledProcessError as e:
            notes = f"power_failed(exit {e.returncode}, make_power.log)"
    _collect_artifacts(sa_dir)
    return time.time() - t0, notes


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


def _also_make_targets(args):
    """--also-make names as given (resolved per workspace by _resolve_targets)."""
    return [t.strip() for t in getattr(args, "also_make", "").split(",") if t.strip()]


def _all_targets(cfg, args):
    return (_build_targets(cfg, args) + _memtile_power_targets(cfg, args)
            + _also_make_targets(args))


def _app_bundle(cfg, args):
    """<--app-bundle-dir>/<config name> if it holds an app bundle, else None."""
    if args.app_bundle_dir:
        b = Path(args.app_bundle_dir).resolve() / _config_name(cfg)
        if (b / "manifest.json").is_file():
            return b
    return None


def _tile_env(cfg, cfg_dir, args):
    """Environment for a config's `mflowgen run` + make: the knobs construct.py
    and common/rtl/gen_rtl.sh read (BUILD_ENV_KEYS)."""
    spec_path = cfg_dir / "spec_config.json"
    env = os.environ.copy()
    env["LAKE_SPEC_CONFIG"] = str(spec_path)
    env["LAKE_SPEC_MODE"] = _mode(cfg)
    env["DUAL_PORT"] = "True" if cfg.get("dual_port", False) else "False"
    env["USE_NON_SPLIT_FIFOS"] = "True" if args.non_split_fifos else "False"
    env["USE_SIM_SRAM"] = "True" if args.use_sim_sram else "False"
    # Genus flatten_effort; unset -> the graph's own default.
    if args.flatten_effort is not None:
        env["FLATTEN"] = str(args.flatten_effort)

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
    bundle = _app_bundle(cfg, args)
    if bundle:
        env["APP_BUNDLE"] = str(bundle)
    return env


def _run_one(cfg, cfg_dir, args):
    t0 = time.time()

    env = _tile_env(cfg, cfg_dir, args)
    if (args.cgra_power or args.include_pnr_power) and not env.get("APP_BUNDLE"):
        # The application step then runs the app on the DEFAULT MemCore
        # (stock container), so the power numbers don't describe this spec.
        print(f"        WARNING: no app bundle for {_config_name(cfg)}"
              f"{' in ' + args.app_bundle_dir if args.app_bundle_dir else ''}: "
              "its power steps replay the app run on the DEFAULT MemCore", flush=True)
    build_targets = _build_targets(cfg, args)
    power_targets = _memtile_power_targets(cfg, args)
    also_targets = _also_make_targets(args)

    make_cmd = ["make", *build_targets]
    power_cmd = ["make", *power_targets]
    jobs = [f"-j{args.parallel_jobs}"] if args.parallel_jobs > 0 else []
    if jobs:
        make_cmd.insert(1, jobs[0])
        power_cmd.insert(1, jobs[0])

    # Steps to force-clean before building (see --clean / --clean-all). These
    # run after `mflowgen run` (so the Makefile + clean-<name> targets exist)
    # and before the build target.
    clean_cmd = _clean_targets(args)

    if args.dry_run:
        dry_env_keys = ["LAKE_SPEC_CONFIG", "LAKE_SPEC_MODE", "DUAL_PORT",
                        "USE_NON_SPLIT_FIFOS", "USE_SIM_SRAM"]
        if args.flatten_effort is not None:
            dry_env_keys += ["FLATTEN"]
        if args.cgra_power:
            dry_env_keys += ["SYNTH_POWER", "RTL_POWER"]
        if args.per_tile:
            dry_env_keys += ["PER_TILE_POWER"]
        if args.memtile_power:
            dry_env_keys += ["MEMTILE_POWER"]
        if env.get("APP_BUNDLE"):
            dry_env_keys += ["APP_BUNDLE"]
        for k in dry_env_keys:
            print(f"        DRY-RUN env: {k}={env[k]}", flush=True)
        print(f"        DRY-RUN cmd: mflowgen run --design {args.graph}",
              flush=True)
        if clean_cmd:
            print(f"        DRY-RUN cmd: {' '.join(clean_cmd)}", flush=True)
        print(f"        DRY-RUN cmd: {' '.join(make_cmd)}", flush=True)
        if power_targets:
            print(f"        DRY-RUN cmd: {' '.join(power_cmd)}", flush=True)
        if also_targets:
            print(f"        DRY-RUN cmd: make {' '.join(jobs + also_targets)}", flush=True)
        return 0.0, ""

    reuse = args.reuse_graph and (cfg_dir / "Makefile").is_file()

    def write_manifest():
        _write_manifest(cfg_dir, cfg, args, "tile", settings=_build_settings(env),
                        targets={"build": build_targets, "memtile_power": power_targets},
                        graph=str(args.graph), graph_reused=reuse)

    write_manifest()    # so a config that fails in `mflowgen run` has one too
    _materialize_graph(cfg_dir, ["mflowgen", "run", "--design", str(args.graph)],
                       env, clean_cmd, reuse, args)

    # Write the spec AFTER any clean. `make clean-all` deletes every file in the
    # workspace except Makefile/.mflowgen* (find -maxdepth 1 ... -exec rm -rf),
    # so writing spec_config.json earlier would let clean-all erase it and make
    # the rtl step fail with "lake_spec_config file not found". mflowgen run only
    # needs the path (baked from LAKE_SPEC_CONFIG env), not the contents.
    _write_spec_files(cfg, cfg_dir, " ".join(build_targets + power_targets),
                      _pnr_role(cfg, args))
    write_manifest()    # now with the graph's step parameters

    for _t in build_targets + power_targets:
        # A reused graph may predate a step: fail this config, not the sweep.
        _check_step_exists(_t, cfg_dir, env, exc=RuntimeError if reuse else SystemExit)
    also_cmd = ["make", *jobs, *_resolve_targets(also_targets, cfg_dir, env)]
    _sh(make_cmd, cwd=cfg_dir, env=env, log=cfg_dir / "make.log")

    notes = []
    if power_targets:
        try:
            _sh(power_cmd, cwd=cfg_dir, env=env, log=cfg_dir / "make_memtile_power.log")
        except subprocess.CalledProcessError as e:
            notes.append(f"memtile_power_failed(exit {e.returncode}, make_memtile_power.log)")
    if also_targets:
        try:
            _sh(also_cmd, cwd=cfg_dir, env=env, log=cfg_dir / "make_also.log")
        except subprocess.CalledProcessError as e:
            notes.append(f"also_make_failed(exit {e.returncode}, make_also.log)")
    notes = " ".join(notes)

    _collect_artifacts(cfg_dir)
    return time.time() - t0, notes


def _write_spec_files(cfg, ws, targets, pnr_role=None):
    """spec_config.json = build_spec kwargs only (util_onyx passes it as
    **kwargs); sweep_meta.json = how the sweep built it (correlation reads
    runtime_mode/targets/pnr_role from it)."""
    with open(ws / "spec_config.json", "w") as f:
        json.dump(_spec_kwargs(cfg), f, indent=2, sort_keys=True)
    meta = {"config_name": _config_name(cfg), "runtime_mode": _mode(cfg),
            "targets": targets}
    if pnr_role:
        meta["pnr_role"] = pnr_role
    with open(ws / "sweep_meta.json", "w") as f:
        json.dump(meta, f, indent=2, sort_keys=True)


# ---------------------------------------------------------------------------
# Build manifest + stale-step check
# ---------------------------------------------------------------------------
# <workspace>/build_manifest.json records everything that went into a build:
# the sweep command line and every parsed flag, the env knobs the sweep
# exported, the spec, the targets, the git state of garnet/lake/mflowgen at
# sweep start, and each graph step's parameters as mflowgen resolved them
# (the `export key=value` lines of .mflowgen/<step>/mflowgen-run, i.e. exactly
# what the step's scripts see). Written after `mflowgen run`, finished with
# the result (+ the rtl step's garnet flags / lake commit) when the build ends.
MANIFEST_FILE = "build_manifest.json"

# Env vars that shape a tile build: what _tile_env exports, plus knobs the
# graphs read from an inherited env. Recorded in the manifest; --skip-existing
# rebuilds a done workspace whose recorded values differ.
BUILD_ENV_KEYS = ("LAKE_SPEC_CONFIG", "LAKE_SPEC_MODE", "DUAL_PORT",
                  "USE_NON_SPLIT_FIFOS", "USE_SIM_SRAM", "FLATTEN",
                  "RTL_POWER", "SYNTH_POWER", "PER_TILE_POWER", "MEMTILE_POWER",
                  "APP_BUNDLE", "LAKE_POND_SPEC_CONFIG", "NO_POND")

_EXPORT_RE = re.compile(r"^export (\w+)=(.*)$")


def _build_settings(env):
    return {k: env[k] for k in BUILD_ENV_KEYS if k in env}


def _read_manifest(ws):
    try:
        return json.loads((ws / MANIFEST_FILE).read_text())
    except (OSError, ValueError):
        return None


def _changed_settings(ws, settings):
    """'KEY a->b, ...' for build settings that differ from the ones recorded
    in ws's manifest; '' if they match or no manifest records them."""
    old = (_read_manifest(ws) or {}).get("settings")
    if old is None:
        return ""
    keys = sorted(set(old) | set(settings))
    return ", ".join(f"{k} {old.get(k)}->{settings.get(k)}"
                     for k in keys if old.get(k) != settings.get(k))


def _step_params(run_script):
    """{param: value} exported by an mflowgen-run script (lists are
    comma-joined, as mflowgen writes them)."""
    params = {}
    for line in _read_lines(run_script):
        m = _EXPORT_RE.match(line)
        if m:
            params[m.group(1)] = m.group(2)
    return params


def _step_dirs(root):
    """<N>-<name> dirs under root, in step-number order."""
    if not root.is_dir():
        return []
    dirs = [d for d in root.iterdir()
            if d.is_dir() and re.match(r"^\d+-", d.name)]
    return sorted(dirs, key=lambda d: int(d.name.split("-", 1)[0]))


def _graph_params(ws):
    """{step: params} as the last `mflowgen run` configured them."""
    return {d.name: _step_params(d / "mflowgen-run")
            for d in _step_dirs(ws / ".mflowgen") if (d / "mflowgen-run").is_file()}


def _stale_steps(ws):
    """[(step, 'param built->now; ...')] for steps that already ran with
    other parameters than the graph now gives them. mflowgen copies the run
    script into the step dir when the step executes, and its make rules do not
    depend on parameters, so make would keep these results."""
    stale = []
    for step, now in _graph_params(ws).items():
        built_dir = ws / step
        if not (built_dir / ".execstamp").exists():
            continue
        built = _step_params(built_dir / "mflowgen-run")
        if not built:
            continue
        diff = [f"{k} {built.get(k)}->{now.get(k)}"
                for k in sorted(set(built) | set(now)) if built.get(k) != now.get(k)]
        if diff:
            stale.append((step, "; ".join(diff)))
    return stale


# What `mflowgen run` writes in a workspace (step dirs are untouched).
GRAPH_FILES = ("Makefile", ".mflowgen", ".mflowgen.yml")
GRAPH_BACKUP = ".mflowgen.prev"   # `make clean-all` spares .mflowgen*


def _materialize_graph(ws, run_cmd, env, clean_cmd, reuse, args):
    """`mflowgen run` (skipped when reuse: --reuse-graph and a Makefile),
    then the --clean targets and the stale-step check. If any of that fails,
    the workspace gets its previous graph back: `mflowgen run` overwrites the
    Makefile and .mflowgen, so a re-run with a changed graph that fails the
    stale check would otherwise leave the workspace unable to make anything
    against the graph its steps were built with (--reuse-graph)."""
    backup = ws / GRAPH_BACKUP
    if reuse:
        print("        reusing the workspace's graph (--reuse-graph): no `mflowgen run`",
              flush=True)
    elif (ws / "Makefile").is_file():
        shutil.rmtree(backup, ignore_errors=True)
        backup.mkdir()
        for name in GRAPH_FILES:
            src = ws / name
            if src.is_dir():
                shutil.copytree(src, backup / name, symlinks=True)
            elif src.exists():
                shutil.copy2(src, backup / name)
    try:
        if not reuse:
            _sh(run_cmd, cwd=ws, env=env, log=ws / "mflowgen_run.log")
        if clean_cmd:
            _sh(clean_cmd, cwd=ws, env=env, log=ws / "make_clean.log")
        _handle_stale_steps(ws, env, args)
    except BaseException:
        if backup.is_dir():
            for name in GRAPH_FILES:
                dst = ws / name
                if dst.is_dir():
                    shutil.rmtree(dst)
                elif dst.exists():
                    dst.unlink()
                if (backup / name).exists():
                    shutil.move(str(backup / name), str(dst))
            print("        restored the workspace's previous graph (Makefile, .mflowgen)",
                  flush=True)
        raise
    finally:
        shutil.rmtree(backup, ignore_errors=True)


def _handle_stale_steps(ws, env, args):
    """Fail on stale steps (see _stale_steps), or clean them with
    --clean-stale so make rebuilds them and everything downstream."""
    stale = _stale_steps(ws)
    if not stale:
        return
    for step, diff in stale:
        print(f"        stale step {step}: {diff}", flush=True)
    if not args.clean_stale:
        raise RuntimeError(
            "built steps have other parameters than the graph now: "
            + ", ".join(step for step, _ in stale)
            + " -- rerun with --clean-stale (rebuilds them) or --fresh")
    steps = [step.split("-", 1)[0] for step, _ in stale]
    _sh(["make", *(f"clean-{n}" for n in steps)], cwd=ws, env=env,
        log=ws / "make_clean_stale.log")


def _git_state(path):
    """Commit, branch, subject and modified tracked files of a git checkout
    (fail-soft: {'path', 'commit': None} when it isn't one)."""
    def git(*a):
        try:
            p = subprocess.run(["git", "-C", str(path), *a], stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            return None
        return p.stdout.strip() if p.returncode == 0 else None
    state = {"path": str(path), "commit": git("rev-parse", "HEAD")}
    if state["commit"]:
        state["branch"] = git("rev-parse", "--abbrev-ref", "HEAD")
        state["subject"] = git("log", "-1", "--format=%s")
        dirty = git("status", "--porcelain", "--untracked-files=no") or ""
        state["modified"] = dirty.splitlines()[:200]
    return state


def _jsonable(v):
    if isinstance(v, (set, frozenset)):
        return sorted(_jsonable(x) for x in v)
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)


def _sweep_provenance(args):
    """Sweep-wide part of every build_manifest.json, taken once at start."""
    try:
        spec = importlib.util.find_spec("mflowgen")
    except (ImportError, ValueError):
        spec = None
    lake = Path(args.lake_dir).resolve()
    lake_state = _git_state(lake)
    if lake_state["commit"]:
        # The container rtl step builds lake origin/THESIS (gen_rtl.sh); this
        # is that ref as of the host lake's last fetch.
        lake_state["origin_THESIS"] = None
        try:
            lake_state["origin_THESIS"] = subprocess.run(
                ["git", "-C", str(lake), "rev-parse", "origin/THESIS"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                timeout=60).stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            pass
    sources = {"garnet": _git_state(GARNET_DIR), "lake": lake_state}
    if spec and spec.origin:
        sources["mflowgen"] = _git_state(Path(spec.origin).resolve().parent.parent)
    derived = ("all_names", "skipped_rv", "provenance")
    return {
        "argv": [sys.executable] + sys.argv,
        "cwd": os.getcwd(),
        "host": socket.gethostname(),
        "user": os.environ.get("USER", ""),
        "pid": os.getpid(),
        "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "mflowgen": shutil.which("mflowgen"),
        "args": {k: _jsonable(v) for k, v in sorted(vars(args).items())
                 if k not in derived},
        "sources": sources,
    }


def _write_manifest(ws, cfg, args, kind, settings, targets, graph,
                    graph_kwargs=None, graph_reused=False):
    manifest = {
        "manifest_version": 1,
        "kind": kind,                       # tile | standalone
        "config_name": _config_name(cfg),
        "runtime_mode": _mode(cfg),
        "pnr_role": _pnr_role(cfg, args) if kind == "tile" else "",
        "spec": _spec_kwargs(cfg),
        "graph": graph,
        "graph_kwargs": _jsonable(graph_kwargs),
        # --reuse-graph kept an older `mflowgen run`: `steps` is what that graph
        # gave each step; `settings` is only this run's request.
        "graph_reused": graph_reused,
        "settings": settings,
        "targets": targets,
        "written": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "sweep": getattr(args, "provenance", None),
        "steps": _graph_params(ws),
        "result": None,
    }
    (ws / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2) + "\n")


def _rtl_provenance(ws):
    """What the rtl step actually ran, from its log: the `aha garnet` flags
    and the lake commit it checked out (container mode; fail-soft)."""
    out = {}
    lines = _read_lines(_first(ws, "*-rtl/mflowgen-run.log"))
    for i, line in enumerate(lines):
        m = re.match(r"^--- (?:DEFAULT rtl build|INTERCONNECT_ONLY): aha garnet (.*)$", line)
        if m:
            out["garnet_flags"] = m.group(1).strip()
        if "changing lake to GF-enabled lake" in line:
            for nxt in lines[i + 1:i + 40]:
                m = re.match(r"^([0-9a-f]{7,40}) (\S.*)$", nxt.strip())
                if m:
                    out["lake_commit"] = f"{m.group(1)} {m.group(2)}"
                    break
    return out


def _finish_manifest(ws, status, notes, duration_s):
    """Add the build's result to ws's manifest (if this run wrote one)."""
    manifest = _read_manifest(ws)
    if manifest is None:
        return
    manifest["result"] = {
        "status": status, "notes": notes,
        "duration_s": None if duration_s is None else round(duration_s, 1),
        "finished": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "executed_steps": [d.name for d in _step_dirs(ws)
                           if (d / ".execstamp").exists()],
        "rtl": _rtl_provenance(ws),
    }
    (ws / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2) + "\n")


def _check_step_exists(step, cfg_dir, env, exc=SystemExit):
    """Validate --stop-after against the configured graph's real targets.

    mflowgen derives make targets from step names, which are not the local
    variable names used in construct.py (e.g. the variable `signoff` is the
    step `cadence-innovus-signoff`). Catching a typo here beats discovering
    it as a bare "No rule to make target" after `mflowgen run` has already
    done its work. A numeric step id is always allowed.
    """
    if str(step).isdigit():
        return
    names, targets = _make_list(cfg_dir, env)

    # If we parsed no step *names*, our parse of `make list` is wrong (or its
    # format changed). Stay quiet rather than block a legitimate build -- make
    # reports an unknown target in about a second anyway.
    if not names or step in targets:
        return

    near = sorted(n for n in names if step in n or n in step)
    hint = f"\n    Did you mean: {', '.join(near)}" if near else ""
    raise exc(
        f"*** ERROR: '{step}' is not a step in this graph.{hint}\n"
        f"    Run `make list` in {cfg_dir} to see all targets.")


def _resolve_targets(items, cfg_dir, env):
    """--also-make names -> make targets: a step name/number as is, else the
    one step whose name ends in -<item> (drc -> mentor-calibre-drc or
    cadence-pegasus-drc; mflowgen's debug-<step> targets don't count).
    Unknown or ambiguous names raise."""
    names, targets = _make_list(cfg_dir, env, steps_only=True)
    if not names:
        return list(items)   # can't parse `make list`; let make complain
    out = []
    for item in items:
        if item in targets:
            out.append(item)
            continue
        hits = sorted(n for n in names if n.endswith("-" + item))
        if len(hits) != 1:
            raise RuntimeError(f"--also-make '{item}': "
                               + (f"ambiguous ({', '.join(hits)})" if hits
                                  else "no such step (see `make list`)"))
        out.append(hits[0])
    return out


def _make_list(cfg_dir, env, steps_only=False):
    """(names, all targets incl. step numbers) from `make list` in a
    configured workspace; two empty sets if it can't be read. names = the
    graph's steps, plus the generic targets unless steps_only."""
    names, targets = set(), set()
    try:
        proc = subprocess.run(["make", "list"], cwd=str(cfg_dir), env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return names, targets
    if proc.returncode != 0:
        return names, targets

    # `make list` prints one node per line as " -  23 : cadence-innovus-signoff"
    # (see mflowgen/backends/makefile_syntax.py: make_list). Generic targets
    # use "-- description" instead of ":". Collect both ids and names.
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
                # Steps are numbered; " - debug-14 : debug-<step>" is not one.
                if num.isdigit() or not steps_only:
                    names.add(name)
        else:
            tok = line.split()[0] if line else ""
            if tok:
                targets.add(tok)
                if not steps_only:
                    names.add(tok)
    return names, targets


# The spec SRAM step (common/gen_sram_macro_spec) and the compiler datasheet
# its collect_datasheet.py links out of genviews-output/.
SRAM_STEP_GLOB = "*-gen_sram_macro_spec"
SRAM_DATASHEET_GLOB = SRAM_STEP_GLOB + "/outputs/sram_datasheet/*"

# Workspace-relative globs for the small subset of files that summarize PPA.
# Shared by _collect_artifacts (copy into artifacts/) and _zip_results.
# Layout/library views of the signoff: most of a PnR config's zip size (the
# merged GDS), and no report reads them. --zip-slim leaves them out.
LAYOUT_GLOBS = [
    "*-cadence-innovus-signoff/outputs/*.lib",
    "*-cadence-innovus-signoff/outputs/*.lef",
    "*-cadence-innovus-signoff/outputs/*.gds",
]
ARTIFACT_GLOBS = LAYOUT_GLOBS + [
    "*-cadence-innovus-signoff/reports/*.rpt",
    # signoff.summary = Innovus's own signoff timing (WNS/TNS per path group).
    "*-cadence-innovus-signoff/reports/*.summary",
    # PT signoff: <design>.timing.{setup,hold}.rpt = top-100 PBA paths;
    # *.report = check_timing/constraints, global timing, clock skew, coverage.
    "*-synopsys-pt-timing-signoff/reports/*.rpt",
    "*-synopsys-pt-timing-signoff/reports/*.report",
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
    # Standalone (lake pd/thesis) idle/active ptpx under --memtile-power; its
    # VCS sims' PASS lines are in their per-step mflowgen-run.log.
    "*-synopsys-ptpx-synth-*-power/outputs/power.*",
    # --app-bundle-dir standalone app power: which app + MEM tile it replayed.
    "*-app-power-gen/outputs/app_stimulus.json",
]

# Extra per-workspace files that only go into the zip: provenance + logs, so a
# failed config can still be debugged on the other machine.
ZIP_EXTRA_GLOBS = [
    "*.json",               # spec_config.json, lake_collateral.json
    "*.log",                # mflowgen_run.log, make_clean.log, make.log (tail)
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
    slim = "_slim" if args.zip_slim else ""
    return out_dir.parent / f"{out_dir.name}_{host}_{stamp}{slim}.zip"


# A workspace's top-level make*.log is make's stdout: every step's output again
# (mflowgen runs steps as `./mflowgen-run 2>&1 | tee mflowgen-run.log`, and the
# per-step logs are zipped) plus make's own lines and the postcondition results.
# Up to MAKE_LOG_FULL_MAX it goes in whole, else only its last lines, which
# hold the failure and the last postconditions.
MAKE_LOG_FULL_MAX = 4 << 20
MAKE_LOG_TAIL_LINES = 2000
# Files this large (merged GDS, Innovus logs) are deflated at level 1: several
# times faster than the default 6 for a slightly bigger zip. Already-compressed
# files are stored as-is.
ZIP_FAST_MIN = 16 << 20
ZIP_STORED_SUFFIXES = (".gz", ".bz2", ".xz", ".zst", ".zip", ".tgz")
ZIP_PROGRESS_S = 30


def _log_tail(path, max_lines):
    """Last max_lines lines of a file (bytes), read backwards from the end."""
    with open(path, "rb") as f:
        pos = f.seek(0, os.SEEK_END)
        data = b""
        while pos > 0 and data.count(b"\n") <= max_lines:
            step = min(1 << 16, pos)
            pos -= step
            f.seek(pos)
            data = f.read(step) + data
    return b"".join(data.splitlines(keepends=True)[-max_lines:])


def _fmt_s(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m // 60}h{m % 60:02d}m" if m >= 60 else f"{m}m{s:02d}s"


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
    tails = set()   # big top-level make*.log: zipped as their last lines
    for name in found:
        for cfg_dir in (out_dir / name, out_dir / STANDALONE_SUBDIR / name):
            seen = set()
            for pat in ZIP_EXTRA_GLOBS + [g for g in ARTIFACT_GLOBS
                                          if not (args.zip_slim and g in LAYOUT_GLOBS)]:
                for src in cfg_dir.glob(pat):
                    if src.is_file() and src not in seen:
                        seen.add(src)
                        files.append(src)
                        if (src.parent == cfg_dir and src.name.startswith("make")
                                and src.suffix == ".log"
                                and src.stat().st_size > MAKE_LOG_FULL_MAX):
                            tails.add(src)
            old = [f for f in _old_sram_datasheets(cfg_dir) if f not in seen]
            files += old
            if any(cfg_dir.glob(SRAM_STEP_GLOB)):
                sram_cfgs += 1
                if not old and not any(f.is_file() for f in
                                       cfg_dir.glob(SRAM_DATASHEET_GLOB)):
                    no_datasheet.append(name)

    zip_path = _default_zip_path(out_dir, args)
    root = zip_path.stem
    total = sum(f.stat().st_size for f in files if f not in tails)
    print(f"\nZipping {len(found)} config(s), {len(files)} file(s), "
          f"{total / 1e9:.2f} GB from {out_dir}\n        -> {zip_path}", flush=True)
    if tails:
        print(f"        {len(tails)} make log(s) over {MAKE_LOG_FULL_MAX >> 20} MB "
              f"go in as their last {MAKE_LOG_TAIL_LINES} lines (the rest repeats "
              f"the per-step logs)", flush=True)
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
            tail = f" (last {MAKE_LOG_TAIL_LINES} lines)" if f in tails else ""
            print(f"        DRY-RUN add: {root}/{f.relative_to(out_dir)}{tail}",
                  flush=True)
        return True

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = zip_path.with_name(zip_path.name + ".partial")
    skipped = 0
    t0 = last = time.time()
    done = 0
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for i, f in enumerate(files, 1):
                arc = f"{root}/{f.relative_to(out_dir)}"
                try:
                    if f in tails:
                        size = f.stat().st_size
                        head = (f"[sweep_specs zip: last {MAKE_LOG_TAIL_LINES} lines of "
                                f"{size / 1e6:.1f} MB; the rest repeats the per-step "
                                f"NN-*/mflowgen-run.log files]\n").encode()
                        zf.writestr(arc, head + _log_tail(f, MAKE_LOG_TAIL_LINES))
                    else:
                        # write() follows symlinks, so mflowgen's outputs/
                        # links are stored as their real contents.
                        size = f.stat().st_size
                        if f.name.endswith(ZIP_STORED_SUFFIXES):
                            zf.write(f, arc, compress_type=zipfile.ZIP_STORED)
                        elif size >= ZIP_FAST_MIN:
                            zf.write(f, arc, compresslevel=1)
                        else:
                            zf.write(f, arc)
                        done += size
                except OSError as e:
                    skipped += 1
                    print(f"        skip {f}: {e}", file=sys.stderr, flush=True)
                now = time.time()
                if now - last >= ZIP_PROGRESS_S:
                    last = now
                    print(f"        zip: {i}/{len(files)} files, {done / 1e9:.2f}/"
                          f"{total / 1e9:.2f} GB in, {tmp.stat().st_size / 1e6:.0f} MB "
                          f"out, {_fmt_s(now - t0)}", flush=True)
        tmp.replace(zip_path)
    except OSError as e:
        print(f"*** ERROR: writing {zip_path} failed: {e}", file=sys.stderr,
              flush=True)
        tmp.unlink(missing_ok=True)
        return False

    size_mb = zip_path.stat().st_size / 1e6
    note = f", {skipped} unreadable file(s) skipped" if skipped else ""
    print(f"Wrote {zip_path} ({size_mb:.1f} MB{note}, {_fmt_s(time.time() - t0)})",
          flush=True)
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
    in ns.

    PT prints in its main library's time unit, which is ps for gf12 (the
    SDC's `set_units -time ns` doesn't change that; the 2026-10-07 smoke run
    reported -1229.256 for a -1.229 ns slack). The report doesn't name the
    unit, so it's read off the capture edges ("clock <c> (rise edge) ... 1333.000"):
    no clock here has a period anywhere near 50 ns, so edges above 50 are ps."""
    slacks, edges = [], []
    for rpt in ws.glob("*-synopsys-pt-timing-signoff/reports/*.timing.setup.rpt"):
        for line in _read_lines(rpt):
            m = re.match(r"^\s*slack\s*\([^)]*\)\s+(-?\d+(?:\.\d+)?)", line)
            if m:
                slacks.append(float(m.group(1)))
            # the edge time is the last column (Path); earlier ones are Trans/Incr
            e = re.match(r"^\s*clock \S+ \((?:rise|fall) edge\)\s.*?(\d+(?:\.\d+)?)\s*$", line)
            if e and float(e.group(1)) > 0:
                edges.append(float(e.group(1)))
    if not slacks:
        return None
    return round(min(slacks) * (1e-3 if edges and min(edges) > 50 else 1.0), 6)


INNOVUS_WNS_GROUPS = ("all", "reg2reg", "in2reg", "reg2out", "in2out")


def _innovus_signoff_wns(ws):
    """Innovus's own signoff setup WNS per path group, in ns, from the
    `Setup mode | all | ... | Reg2Reg |` table of the signoff step's
    reports/signoff.summary (the foundation flow's timeDesign -signoff; the
    table lake's THESIS/pipeline/tile_sweep.py reads too). Independent of PT:
    still there for sweeps that stopped at cadence-innovus-signoff."""
    out = {f"tile_pnr_innovus_wns_{g}_ns": None for g in INNOVUS_WNS_GROUPS}
    lines = _read_lines(_first(ws, "*-cadence-innovus-signoff/reports/signoff.summary"))
    hdr = next((i for i, l in enumerate(lines) if "Setup mode" in l and "|" in l), None)
    if hdr is None:
        return out
    row = next((l for l in lines[hdr + 1:] if "WNS (ns):" in l), None)
    if row is None:
        return out
    cols = [c.strip().lower() for c in lines[hdr].split("|")[2:-1]]
    for c, v in zip(cols, (v.strip() for v in row.split("|")[2:-1])):
        if c in INNOVUS_WNS_GROUPS:
            try:
                out[f"tile_pnr_innovus_wns_{c}_ns"] = float(v)
            except ValueError:
                pass   # N/A: no paths in that group
    return out


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
        **_innovus_signoff_wns(ws),
    }


def _sweep_meta(ws, name):
    """runtime_mode/targets/pnr_role a workspace was built with
    (sweep_meta.json); workspaces from before it existed fall back to the name
    suffix (and no role)."""
    try:
        meta = json.loads((ws / "sweep_meta.json").read_text())
    except (OSError, ValueError):
        meta = {}
    mode = meta.get("runtime_mode") or ("rv" if name.endswith("_rv") else "static")
    return {"runtime_mode": mode, "targets": meta.get("targets", ""),
            "pnr_role": meta.get("pnr_role", "")}


def _apply_roles(rows, validate_names):
    """--validate-set, when given, overrides the pnr_role recorded at build
    time. Only 'validate' matters to the fits: those rows are left out of them
    and their PnR results are predicted instead."""
    if validate_names is None:
        return
    for r in rows:
        if r["config_name"] in validate_names:
            r["pnr_role"] = "validate"
        elif r["pnr_role"] == "validate":
            r["pnr_role"] = "fit"


# Tile synth -> tile PnR fits: (label, synth column, PnR column). Both sides
# are instance areas (Genus cell area vs Innovus signoff instance area). The
# die itself is sized from synth area at floorplan (fixed height, width =
# area/density), so it carries no extra information. `logic` drops the SRAM
# macros, which are identical in synth and PnR.
PNR_FITS = (
    ("total", "tile_synth_cell_area", "tile_pnr_total_area"),
    ("logic", "tile_synth_logic_area", "tile_pnr_logic_area"),
)
# PnR total area as synth SRAM macro area + the `logic` fit's projection: the
# macros carry over unchanged, so they are not scaled by a fitted slope (the
# `total` fit does scale them).
VIA_LOGIC_COL = "tile_pnr_total_area_proj_via_logic"
# --memtile-power: idle/active power of the Genus netlist -> of the signoff one.
POWER_FITS = tuple((f"{v}_power", f"synth_{v}_total_power", f"pnr_{v}_total_power")
                   for v in MEMTILE_POWER_VARIANTS)
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


def _pct_err(pred, actual):
    """(pred - actual) / actual in %, None unless both are numbers."""
    if not isinstance(pred, float) or not isinstance(actual, float) or not actual:
        return None
    return (pred - actual) / actual * 100


def _fit_and_project(rows, fits=PNR_FITS):
    """Fit PnR on synth per group (all / static / rv) over the rows that have
    both and are not held out (pnr_role 'validate'), then add the projected
    PnR value to every row with a synth value. A row uses its own mode's fit
    when that has MIN_FIT_POINTS, else the pooled one; proj_extrapolated flags
    synth values outside the fitted range; proj_err_pct = (projected - actual)
    / actual where PnR ran: the in-sample residual for fit rows, the prediction
    error for held-out ones. Returns the fit-table rows; val_* = the held-out
    rows' prediction errors under that fit."""
    groups = {"all": rows}
    for mode in RUNTIME_MODES:
        groups[mode] = [r for r in rows if r["runtime_mode"] == mode]
    table, fitted = [], {}
    for label, xcol, ycol in fits:
        for group, members in groups.items():
            pts = [(r[xcol], r[ycol]) for r in members
                   if r.get("pnr_role") != "validate"
                   and isinstance(r.get(xcol), float) and isinstance(r.get(ycol), float)]
            fit = _linfit(pts)
            fitted[(label, group)] = fit
            if fit:
                table.append({"metric": label, "group": group,
                              "synth_column": xcol, "pnr_column": ycol, **fit})
    for r in rows:
        for label, xcol, ycol in fits:
            fit, used = fitted.get((label, r["runtime_mode"])), r["runtime_mode"]
            if not fit:
                fit, used = fitted.get((label, "all")), "all"
            x = r.get(xcol)
            if fit and isinstance(x, float):
                r[f"{ycol}_proj"] = fit["intercept"] + fit["slope"] * x
                r[f"{ycol}_proj_fit"] = used
                r[f"{ycol}_proj_extrapolated"] = (
                    "yes" if not fit["x_min"] <= x <= fit["x_max"] else "no")
            else:
                r[f"{ycol}_proj"] = None
                r[f"{ycol}_proj_fit"] = ""
                r[f"{ycol}_proj_extrapolated"] = ""
            r[f"{ycol}_proj_err_pct"] = _pct_err(r[f"{ycol}_proj"], r.get(ycol))
    for t in table:
        col = t["pnr_column"]
        errs = [abs(r[f"{col}_proj_err_pct"]) for r in rows
                if r.get("pnr_role") == "validate" and r[f"{col}_proj_fit"] == t["group"]
                and r[f"{col}_proj_err_pct"] is not None]
        t["val_n"] = len(errs)
        t["val_mean_abs_pct_err"] = sum(errs) / len(errs) if errs else None
        t["val_max_abs_pct_err"] = max(errs) if errs else None
    return table


def _write_csv(path, rows, fmt="{:.3f}"):
    rows = [{k: (fmt.format(v) if isinstance(v, float) else v) for k, v in r.items()}
            for r in rows]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _print_fits(table):
    pct = lambda v: "n/a" if v is None else f"{v:.2f}%"  # noqa: E731
    for t in table:
        held = (f"   held-out n={t['val_n']} |err| mean {pct(t['val_mean_abs_pct_err'])} "
                f"max {pct(t['val_max_abs_pct_err'])}" if t["val_n"] else "")
        print(f"  {t['metric']:12s} {t['group']:6s} n={t['n']:<3d} "
              f"pnr = {t['slope']:.4g} * synth + {t['intercept']:.4g}   "
              f"R^2={t['r2']:.4f}   |err| mean {pct(t['mean_abs_pct_err'])} "
              f"max {pct(t['max_abs_pct_err'])}{held}", flush=True)


def _validation_rows(rows, metrics):
    """pnr_validation.csv rows: per held-out config and metric, the synth
    value, the PnR value the model predicts, the real one and the error.
    metrics: (metric, synth column, PnR column, projected column, column
    whose fit made the projection)."""
    out = []
    for r in rows:
        if r.get("pnr_role") != "validate":
            continue
        for metric, xcol, ycol, pcol, fcol in metrics:
            out.append({
                "config_name": r["config_name"], "runtime_mode": r["runtime_mode"],
                "metric": metric, "synth": r.get(xcol),
                "pnr_predicted": r.get(pcol), "pnr_actual": r.get(ycol),
                "err_pct": _pct_err(r.get(pcol), r.get(ycol)),
                "fit": r.get(f"{fcol}_proj_fit", ""),
                "extrapolated": r.get(f"{fcol}_proj_extrapolated", ""),
            })
    return out


def _write_correlation(out_dir, names, validate_names=None):
    """Write <out_dir>/correlation.csv: per config, standalone synth vs tile
    synth vs tile PnR area/slack, pulled from whichever workspaces exist, plus
    PnR area projected from tile synth area; and correlation_fit.csv, the
    synth->PnR fits behind the projection (once >= MIN_FIT_POINTS configs
    have both). Returns the held-out configs' pnr_validation.csv rows."""
    rows = []
    for name in names:
        row = {"config_name": name}
        row.update(_sweep_meta(out_dir / name, name))
        row.update(_synth_metrics(out_dir / STANDALONE_SUBDIR / name, "standalone_synth"))
        row.update(_synth_metrics(out_dir / name, "tile_synth"))
        row.update(_pnr_metrics(out_dir / name))
        rows.append(row)
    if not rows:
        return []
    _apply_roles(rows, validate_names)
    table = _fit_and_project(rows)
    for r in rows:
        sram, logic = r["tile_synth_sram_area"], r["tile_pnr_logic_area_proj"]
        r[VIA_LOGIC_COL] = (sram + logic if isinstance(sram, float)
                            and isinstance(logic, float) else None)
        r[VIA_LOGIC_COL + "_err_pct"] = _pct_err(r[VIA_LOGIC_COL], r["tile_pnr_total_area"])
    path = out_dir / "correlation.csv"
    _write_csv(path, rows)
    print(f"Correlation: {path}", flush=True)
    if table:
        fit_path = out_dir / "correlation_fit.csv"
        _write_csv(fit_path, table)
        print(f"Synth->PnR fit: {fit_path}", flush=True)
        _print_fits(table)
    return _validation_rows(rows, [
        ("total_area", "tile_synth_cell_area", "tile_pnr_total_area",
         "tile_pnr_total_area_proj", "tile_pnr_total_area"),
        ("total_area_via_logic", "tile_synth_cell_area", "tile_pnr_total_area",
         VIA_LOGIC_COL, "tile_pnr_logic_area"),
        ("logic_area", "tile_synth_logic_area", "tile_pnr_logic_area",
         "tile_pnr_logic_area_proj", "tile_pnr_logic_area"),
    ])


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
        # One window for both variants (same stimulus) since 2026-10-06;
        # older power_tests.json kept it per variant.
        row[f"{variant}_window_cycles"] = meta.get(
            "window", meta.get("variants", {}).get(variant, {}).get("window"))
    for level in ("synth", "pnr"):
        total = {}
        for variant in MEMTILE_POWER_VARIANTS:
            n = _top_row_nums(_first(ws, f"*-memtile-power-{level}-{variant}/outputs/power.hier"))
            for i, part in enumerate(("internal", "switching", "leakage", "total")):
                row[f"{level}_{variant}_{part}_power"] = n[i] if len(n) >= 4 else None
            total[variant] = n[3] if len(n) >= 4 else None
        idle, active = total["idle"], total["active"]
        row[f"{level}_active_over_idle"] = active / idle if idle and active is not None else None
    return row


def _standalone_power_metrics(sa_ws):
    """Lake's idle/active power of the standalone synth netlist
    (synopsys-ptpx-synth-{idle,active}-power, top row = lakespec), and the
    app-driven power (synopsys-ptpx-synth-app-power: one MEM tile of an app
    bundle replayed into the lakespec; standalone_app = app:tile)."""
    row, total = {}, {}
    try:
        stim = json.loads(_first(sa_ws, "*-app-power-gen/outputs/app_stimulus.json").read_text())
        row["standalone_app"] = f"{stim.get('app')}:{stim.get('tile')}"
    except (AttributeError, OSError, ValueError):
        row["standalone_app"] = None
    for variant in MEMTILE_POWER_VARIANTS + ("app",):
        n = _top_row_nums(_first(sa_ws, f"*-synopsys-ptpx-synth-{variant}-power/outputs/power.hier"))
        for i, part in enumerate(("internal", "switching", "leakage", "total")):
            row[f"standalone_{variant}_{part}_power"] = n[i] if len(n) >= 4 else None
        total[variant] = n[3] if len(n) >= 4 else None
    idle, active = total["idle"], total["active"]
    row["standalone_active_over_idle"] = active / idle if idle and active is not None else None
    row["standalone_app_over_idle"] = (total["app"] / idle
                                       if idle and total["app"] is not None else None)
    return row


def _tile_app_power_metrics(ws, standalone_app):
    """App-driven Tile_MemCore power (--cgra-power with an app bundle):
    tile-post-{rtl,synth,pnr}-power write one report per placed MEM tile
    (outputs/reports/<Tile_X.._Y..>.hier). tile_app = the tile reported: the
    one the standalone replay used (standalone_app = app:tile), else the
    first."""
    row = {"tile_app": None}
    want = standalone_app.rsplit(":", 1)[-1] if standalone_app else None
    for level in ("rtl", "synth", "pnr"):
        reps = sorted(ws.glob(f"*-post-{level}-power/outputs/reports/Tile_X*.hier"))
        pick = next((r for r in reps if r.stem == want), reps[0] if reps else None)
        # the tile's own row (ptpx-rtl's -verbose report puts a wireload
        # table first, so not simply the first row after a rule)
        n = next((_nums(l) for l in _read_lines(pick)
                  if l.split()[:1] in (["Tile_MemCore"], ["Tile_PE"]) and len(_nums(l)) >= 4), [])
        row[f"tile_{level}_app_total_power"] = n[3] if len(n) >= 4 else None
        if pick is not None and row["tile_app"] is None:
            row["tile_app"] = pick.stem
    return row


def _write_memtile_power(out_dir, names, validate_names=None):
    """<out_dir>/memtile_power.csv: idle + active Tile_MemCore power per
    config (--memtile-power), synth and PnR netlists, with the PnR power
    projected from the synth power (memtile_power_fit.csv), like the area in
    correlation.csv, and the standalone spec's idle + active power (lake's
    tests on its synth netlist) when --standalone-synth built them.
    Fail-soft: blank cells for anything not built. Returns the held-out
    configs' pnr_validation.csv rows."""
    rows = []
    for name in names:
        ws, sa_ws = out_dir / name, out_dir / STANDALONE_SUBDIR / name
        if not (_first(ws, "*-memtile-power-test-gen")
                or _first(sa_ws, "*-synopsys-ptpx-synth-*-power")
                or _first(ws, "*-post-*-power/outputs/reports/Tile_X*.hier")):
            continue
        row = {"config_name": name}
        row.update(_sweep_meta(ws, name))
        row.update(_memtile_power_metrics(ws))
        row.update(_standalone_power_metrics(sa_ws))
        row.update(_tile_app_power_metrics(ws, row.get("standalone_app")))
        rows.append(row)
    if not rows:
        return []
    _apply_roles(rows, validate_names)
    table = _fit_and_project(rows, POWER_FITS)
    # 6 significant digits: a fixed 3 decimals would zero sub-mW powers.
    path = out_dir / "memtile_power.csv"
    _write_csv(path, rows, fmt="{:.6g}")
    print(f"MemTile idle/active power: {path}", flush=True)
    if table:
        fit_path = out_dir / "memtile_power_fit.csv"
        _write_csv(fit_path, table, fmt="{:.6g}")
        print(f"Synth->PnR power fit: {fit_path}", flush=True)
        _print_fits(table)
    return _validation_rows(rows, [(label, x, y, y + "_proj", y) for label, x, y in POWER_FITS])


def _write_reports(out_dir, names, args):
    """correlation.csv, memtile_power.csv (each + its *_fit.csv) and, when
    PnR configs are held out of the fits (--validate-set), pnr_validation.csv:
    the model's PnR prediction vs the real PnR result for each of them."""
    validate = getattr(args, "validate_names", None)
    val = _write_correlation(out_dir, names, validate)
    val += _write_memtile_power(out_dir, names, validate)
    if not val:
        return
    path = out_dir / "pnr_validation.csv"
    _write_csv(path, val, fmt="{:.6g}")
    print(f"PnR prediction vs held-out PnR: {path}", flush=True)
    for metric in dict.fromkeys(v["metric"] for v in val):
        errs = [abs(v["err_pct"]) for v in val
                if v["metric"] == metric and v["err_pct"] is not None]
        pending = sum(1 for v in val if v["metric"] == metric and v["err_pct"] is None)
        stats = (f"|err| mean {sum(errs) / len(errs):.2f}% max {max(errs):.2f}%"
                 if errs else "no PnR result yet")
        print(f"  {metric:22s} n={len(errs)}{f' (+{pending} pending)' if pending else ''}"
              f"  {stats}", flush=True)


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
