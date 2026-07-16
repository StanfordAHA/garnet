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
derives mem_width = data_width * vec_width and mem_depth from
storage_capacity. Only keys that file reads have any effect on the RTL:
vec_width, data_width, storage_capacity (plus dual_port via its own env
knob). The remaining keys are recorded for provenance and to keep config
names aligned with the collateral sweeps in aha.

Requires a garnet whose garnet.py accepts --lake-spec-config (i.e. the
modern_gf lineage). On a garnet without it, the rtl step fails in argparse.

Examples:
    # List what would run, touch nothing
    ./mflowgen/sweep_specs.py --dry-run

    # Single smoke point, RTL only
    ./mflowgen/sweep_specs.py --rtl-only --only fw1_dw16_sc4096_sp_in1_out1

    # Full sweep through signoff, 8-way make
    ./mflowgen/sweep_specs.py --parallel-jobs 8
"""

from pathlib import Path
import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time


# Directory holding this script == <garnet>/mflowgen. Everything path-related
# is derived from it so the script is relocatable across machines.
MFLOWGEN_DIR = Path(__file__).resolve().parent
GARNET_DIR = MFLOWGEN_DIR.parent


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
    p.add_argument("--runtime-mode", choices=["static", "rv"], default="static",
                   help="Lake runtime mode -> --lake-spec-mode (default: %(default)s).")
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
    p.add_argument("--only", default="",
                   help="Comma-separated config names to include.")
    p.add_argument("--skip", default="",
                   help="Comma-separated config names to exclude.")
    p.add_argument("--parallel-jobs", type=int, default=0,
                   help="If >0, pass -j N to `make` inside each workspace.")
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
    p.add_argument("--dry-run", action="store_true",
                   help="Print each config's workspace + commands, run nothing.")
    p.add_argument("--skip-existing", action="store_true",
                   help="Skip configs whose workspace already has done.flag.")
    p.add_argument("--list", action="store_true",
                   help="Print the selected config names and exit.")
    return p


def main(argv=None):
    args = build_argparser().parse_args(argv)

    if args.rtl_only:
        args.stop_after = "rtl"

    configs = _collect_configs(args)
    if not configs:
        print("No spec points selected; nothing to do.", flush=True)
        return 0

    if args.list:
        for cfg in configs:
            print(_config_name(cfg))
        return 0

    _preflight(args)

    out_dir = Path(args.out_dir).resolve()
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
    results_csv = out_dir / "results.csv"

    print(f"garnet:   {GARNET_DIR}", flush=True)
    print(f"graph:    {args.graph}", flush=True)
    print(f"out_dir:  {out_dir}", flush=True)
    print(f"Sweeping {len(configs)} spec point(s).", flush=True)

    rows = []
    failures = 0
    for i, cfg in enumerate(configs, start=1):
        name = _config_name(cfg)
        cfg_dir = out_dir / name
        if not args.dry_run:
            cfg_dir.mkdir(parents=True, exist_ok=True)
        done_flag = cfg_dir / "done.flag"

        print(f"\n[{i}/{len(configs)}] {name}", flush=True)
        print(f"        workspace: {cfg_dir}", flush=True)

        if args.skip_existing and done_flag.exists():
            print("        SKIP: done.flag already present", flush=True)
            rows.append(_row(name, cfg, cfg_dir, "SKIP", "already_done", 0.0))
            _write_results(results_csv, rows)
            continue

        try:
            duration = _run_one(cfg, cfg_dir, args)
            if args.dry_run:
                continue
            done_flag.write_text("ok\n")
            rows.append(_row(name, cfg, cfg_dir, "PASS", "", duration))
        except subprocess.CalledProcessError as e:
            failures += 1
            rows.append(_row(name, cfg, cfg_dir, "FAIL",
                             f"exit_code={e.returncode}", 0.0))
        except Exception as e:  # noqa: BLE001 -- record and press on
            failures += 1
            rows.append(_row(name, cfg, cfg_dir, "FAIL", str(e)[:200], 0.0))
        _write_results(results_csv, rows)

    if args.dry_run:
        print("\nDry run: nothing executed.", flush=True)
        return 0

    print(f"\nDone: {len(rows) - failures} ok, {failures} failed. "
          f"Results: {results_csv}", flush=True)
    return 1 if failures else 0


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


# ---------------------------------------------------------------------------
# Config selection
# ---------------------------------------------------------------------------
def _collect_configs(args):
    configs = [] if args.replace else list(DEFAULT_SPEC_POINTS)

    if args.extra_specs:
        with open(args.extra_specs) as f:
            payload = json.load(f)
        if not isinstance(payload, list):
            raise SystemExit(f"*** ERROR: --extra-specs must be a JSON list, "
                             f"got {type(payload).__name__}")
        configs.extend(payload)

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
    """Stable name per spec point. Matches the naming used by the collateral
    sweeps in aha, so per-config dirs line up across both."""
    fw = cfg.get("vec_width", 4)
    dw = cfg.get("data_width", 16)
    sc = cfg.get("storage_capacity", 4096)
    dp = cfg.get("dual_port", False)
    inp = cfg.get("in_ports", 2)
    outp = cfg.get("out_ports", 2)
    vc = cfg.get("vec_capacity", 2)
    dims = cfg.get("dims", 6)
    me = cfg.get("max_extent")

    parts = [f"fw{fw}_dw{dw}_sc{sc}"]
    parts.append("dp" if dp else "sp")
    parts.append(f"in{inp}_out{outp}")
    if fw > 1:
        parts.append(f"vc{vc}")
    if dims != 6:
        parts.append(f"dim{dims}")
    if me is not None:
        parts.append(f"me{me}")
    return "_".join(parts)


# ---------------------------------------------------------------------------
# Per-config runner
# ---------------------------------------------------------------------------
def _run_one(cfg, cfg_dir, args):
    t0 = time.time()

    spec_path = cfg_dir / "spec_config.json"
    env = os.environ.copy()
    env["LAKE_SPEC_CONFIG"] = str(spec_path)
    env["LAKE_SPEC_MODE"] = args.runtime_mode
    env["DUAL_PORT"] = "True" if cfg.get("dual_port", False) else "False"
    env["USE_NON_SPLIT_FIFOS"] = "True" if args.non_split_fifos else "False"
    env["USE_SIM_SRAM"] = "True" if args.use_sim_sram else "False"

    make_cmd = ["make", str(args.stop_after)]
    if args.parallel_jobs > 0:
        make_cmd.insert(1, f"-j{args.parallel_jobs}")

    if args.dry_run:
        for k in ("LAKE_SPEC_CONFIG", "LAKE_SPEC_MODE", "DUAL_PORT",
                  "USE_NON_SPLIT_FIFOS", "USE_SIM_SRAM"):
            print(f"        DRY-RUN env: {k}={env[k]}", flush=True)
        print(f"        DRY-RUN cmd: mflowgen run --design {args.graph}",
              flush=True)
        print(f"        DRY-RUN cmd: {' '.join(make_cmd)}", flush=True)
        return 0.0

    with open(spec_path, "w") as f:
        json.dump(cfg, f, indent=2, sort_keys=True)

    _sh(["mflowgen", "run", "--design", str(args.graph)],
        cwd=cfg_dir, env=env, log=cfg_dir / "mflowgen_run.log")
    _check_step_exists(args.stop_after, cfg_dir, env)
    _sh(make_cmd, cwd=cfg_dir, env=env, log=cfg_dir / "make.log")

    _collect_artifacts(cfg_dir)
    return time.time() - t0


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

    targets = set()
    for line in proc.stdout.splitlines():
        line = line.strip().lstrip("-").strip()
        tok = line.split()[0] if line else ""
        if tok:
            targets.add(tok)
    if not targets or step in targets:
        return

    near = sorted(t for t in targets if step in t or t in step)
    hint = f"\n    Did you mean: {', '.join(near)}" if near else ""
    raise SystemExit(
        f"*** ERROR: '{step}' is not a step in this graph.{hint}\n"
        f"    Run `make list` in {cfg_dir} to see all targets.")


def _collect_artifacts(cfg_dir):
    """Copy the small subset of files that summarize PPA into artifacts/."""
    art = cfg_dir / "artifacts"
    art.mkdir(exist_ok=True)

    interesting_globs = [
        "*-cadence-innovus-signoff/outputs/*.lib",
        "*-cadence-innovus-signoff/outputs/*.lef",
        "*-cadence-innovus-signoff/outputs/*.gds",
        "*-cadence-innovus-signoff/reports/*.rpt",
        "*-cadence-innovus-signoff/reports/*.summary",
        "*-synopsys-pt-timing-signoff/reports/*.rpt",
        "*-tile-post-pnr-power/reports/*.rpt",
        "*-cadence-genus-synthesis/reports/*.rpt",
    ]
    for pat in interesting_globs:
        for src in cfg_dir.glob(pat):
            dst = art / src.parent.parent.name / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, dst)
            except OSError:
                pass


def _sh(cmd, cwd, env, log):
    """Run a command tee-ing to a log file; raise on non-zero exit."""
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    print(f"        $ {' '.join(cmd)}  (log: {log.name})", flush=True)
    with open(log, "w") as f:
        proc = subprocess.run(cmd, cwd=str(cwd), env=env,
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


def _row(name, cfg, cfg_dir, status, notes, duration_s):
    return {
        "config_name": name,
        "storage_capacity": cfg.get("storage_capacity", 4096),
        "data_width": cfg.get("data_width", 16),
        "vec_width": cfg.get("vec_width", 4),
        "in_ports": cfg.get("in_ports", 2),
        "out_ports": cfg.get("out_ports", 2),
        "dual_port": cfg.get("dual_port", False),
        "vec_capacity": cfg.get("vec_capacity", 2),
        "status": status,
        "duration_s": f"{duration_s:.1f}",
        "workspace": str(cfg_dir),
        "notes": notes,
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
