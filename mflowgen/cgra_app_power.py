#!/usr/bin/env python3
"""Whole-CGRA post-synthesis power of one app recorded in several variants
(e.g. two mappings of conv_3_3), each variant replayed on the SAME synthesized
tiles, so the variants differ only in activity.

    ./mflowgen/cgra_app_power.py \\
        --variants A=<bundles>/A,B=<bundles>/B --out-dir ~/cgra_app_power

Each variant is an app-bundle directory laid out as sweep_specs.py
--app-bundle-dir reads it (<dir>/<config>/manifest.json, ...; recorded in /aha
by common/application/gen_app_bundle.py, see mflowgen/CLAUDE.md "App bundles").
For every config found in all variants it builds one Tile_MemCore and one
Tile_PE workspace (<out-dir>/<config>/<tile>) with the bundles' spec and mode,
synthesizes each once, and replays every variant on it:

    APP_BUNDLE_VARIANTS=A=...,B=... (common/app_variants.py)
    make post-synth-power-A post-synth-power-B ...

then adds up the per-tile reports (outputs/reports/<tile>.{hier,cell,replay.json})
into <out-dir>/cgra_power.csv (one row per config x variant) and
<out-dir>/cgra_power_tiles.csv (one row per replayed tile):

  placed      tiles with a placed MEM/PE core
  route       tiles only the app's routes pass through   (bundles made with
  idle        one untouched tile per type, scaled to       gen_app_bundle.py
              every tile the app does not touch            --cgra-tiles)
  app_W       placed + route;  array_W = app_W + idle x untouched tiles
  sram_W      SRAM macro power (cell rows matching --sram-cell-re)
  window_s    the replay's activity window (stall release -> $finish), so
  app_J       sum of each tile's power x window = energy of one app run
  d_*_pct     change against the first variant

Bundles without --cgra-tiles give placed tiles only (route/idle columns empty).
Every tile must replay its recording exactly (run_all_tiles.py replay_check);
a failing post-synth-power-<variant> step fails that workspace, and the CSVs
mark tiles that did not replay. Needs the build machine (Genus, Xcelium,
PrimeTime, the ADK, docker for the rtl step), like sweep_specs.py --cgra-power.
--report-only re-reads existing workspaces (also on /aha, from a copied
--zip archive).
"""
import argparse
import csv
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import zipfile
from pathlib import Path

MFLOWGEN_DIR = Path(__file__).resolve().parent
GARNET_DIR = MFLOWGEN_DIR.parent
TILES = ("Tile_MemCore", "Tile_PE")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--variants", default=None, metavar="NAME=DIR,...",
                   help="variant name = app-bundle dir (<dir>/<config>/manifest.json), "
                        "comma separated; the first is the reference for the d_* columns")
    p.add_argument("--out-dir", required=True,
                   help="workspaces + CSVs; keep it outside the garnet checkout")
    p.add_argument("--config", action="append", default=[],
                   help="config name(s) to run (default: every config all variants have)")
    p.add_argument("--tiles", default=",".join(TILES),
                   help="tile graphs to build (default both)")
    p.add_argument("--parallel-jobs", type=int, default=4, help="make -j per workspace")
    p.add_argument("--tile-jobs", type=int, default=2,
                   help="workspaces built at once (default 2: MEM and PE together)")
    p.add_argument("--clock-mhz", type=float, default=750.0,
                   help="the array clock, for synthesis and the replays of every tile "
                        "(Tile_MemCore env CLOCK_PERIOD, Tile_PE clock_period_PE; their own "
                        "defaults differ: 1.333 / 1.1 ns); default 750 MHz")
    p.add_argument("--flatten-effort", type=int, default=None, help="env FLATTEN")
    p.add_argument("--sram-cell-re", default=r"^IN12LP_",
                   help="cell-report reference names counted as SRAM macro (default gf12 "
                        "IN12LP_* macros)")
    p.add_argument("--clean", default="",
                   help="comma list of steps to `make clean-<step>` first (e.g. rtl after a "
                        "lake/garnet pull)")
    p.add_argument("--report-only", action="store_true",
                   help="only (re)write the CSVs from existing workspaces")
    p.add_argument("--dry-run", action="store_true", help="print what would run")
    p.add_argument("--zip", action="store_true",
                   help="afterwards, zip CSVs + per-tile reports + logs (no workspaces) to "
                        "<out-dir>_<host>_<time>.zip for copying back to /aha")
    return p.parse_args(argv)


# ------------------------------------------------------------- variants ----

def parse_variants(text):
    out = []
    for item in filter(None, (s.strip() for s in (text or "").split(","))):
        name, sep, path = item.partition("=")
        if not sep or not re.fullmatch(r"[A-Za-z0-9_]+", name) or not path:
            raise SystemExit(f"*** --variants: bad entry {item!r} (want NAME=DIR, NAME in [A-Za-z0-9_])")
        if name in dict(out):
            raise SystemExit(f"*** --variants: {name} given twice")
        out.append((name, Path(path).expanduser().resolve()))
    return out


def configs_of(variants, wanted):
    """Configs every variant has a bundle for (or `wanted`, checked)."""
    have = [{d.name for d in v.iterdir() if (d / "manifest.json").is_file()} if v.is_dir() else set()
            for _, v in variants]
    common = set.intersection(*have) if have else set()
    if wanted:
        names = [n for w in wanted for n in w.split(",") if n]
        missing = [(n, v) for n in names for (v, _), h in zip(variants, have) if n not in h]
        if missing:
            raise SystemExit("*** no bundle for " + ", ".join(f"{n} in variant {v}" for n, v in missing))
        return names
    if not common:
        raise SystemExit("*** the variants share no config (each needs <dir>/<config>/manifest.json)")
    return sorted(common)


def load_manifests(variants, config):
    """{variant: manifest}; all must describe the same spec + mode."""
    mans = {v: json.load(open(d / config / "manifest.json")) for v, d in variants}
    ref_v, ref = next(iter(mans.items()))
    for v, m in mans.items():
        for key in ("spec_config", "mode", "pond_spec"):
            if m.get(key) != ref.get(key):
                raise SystemExit(f"*** {config}: variant {v}'s {key} differs from {ref_v}'s; "
                                 "variants must replay on the same tiles")
    return mans


# ---------------------------------------------------------------- build ----

def tile_env(tile, ws, man, variants, config, args):
    """Environment of one tile workspace: what sweep_specs.py gives a tile
    build (_tile_env), plus the variants."""
    env = os.environ.copy()
    for k in ("APP_BUNDLE", "RTL_POWER", "MEMTILE_POWER", "LAKE_SPEC_CONFIG", "LAKE_SPEC_MODE",
              "LAKE_POND_SPEC_CONFIG"):
        env.pop(k, None)
    spec = man["spec_config"]
    # a bundle recorded with a PE-tile spec pond (gen_app_bundle.py --pond-spec)
    # replays on a Tile_PE built with that pond (check_bundle compares them)
    if tile == "Tile_PE" and man.get("pond_spec") is not None:
        env["LAKE_POND_SPEC_CONFIG"] = str(ws / "pond_spec.json")
    # Tile_PE: a static bundle replays on the default PE tile; an RV bundle's
    # PE tiles carry the RV spec pond (mflowgen/CLAUDE.md "Bundle guards").
    if tile == "Tile_MemCore" or man["mode"] == "rv":
        env["LAKE_SPEC_CONFIG"] = str(ws / "spec_config.json")
        env["LAKE_SPEC_MODE"] = man["mode"]
    env["DUAL_PORT"] = "True" if spec.get("dual_port", False) else "False"
    env["USE_NON_SPLIT_FIFOS"] = "True"
    env["USE_SIM_SRAM"] = "False"
    env["SYNTH_POWER"] = "True"
    env["APP_BUNDLE_VARIANTS"] = ",".join(f"{v}={d / config}" for v, d in variants)
    if args.flatten_effort is not None:
        env["FLATTEN"] = str(args.flatten_effort)
    period = f"{round(1e6 / args.clock_mhz) / 1000:g}"
    env["CLOCK_PERIOD"] = period      # Tile_MemCore
    env["clock_period_PE"] = period   # Tile_PE
    # construct.py imports mflowgen/common
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(MFLOWGEN_DIR), env.get("PYTHONPATH")) if p)
    return env


def sh(cmd, cwd, env, log):
    print(f"    [{cwd.parent.name}/{cwd.name}] $ {' '.join(cmd)}  (log {log.name})", flush=True)
    with open(log, "w") as f:
        rc = subprocess.run(cmd, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
                            stdout=f, stderr=subprocess.STDOUT).returncode
    if rc:
        tail = log.read_text(errors="replace").splitlines()[-15:]
        raise RuntimeError(f"{' '.join(cmd[:2])} rc={rc}\n      " + "\n      ".join(tail))


def build_tile(tile, config, variants, man, args, status):
    ws = Path(args.out_dir).resolve() / config / tile
    t0 = time.time()
    try:
        if args.dry_run:
            env = tile_env(tile, ws, man, variants, config, args)
            for k in ("LAKE_SPEC_CONFIG", "LAKE_SPEC_MODE", "LAKE_POND_SPEC_CONFIG", "APP_BUNDLE_VARIANTS",
                      "CLOCK_PERIOD", "clock_period_PE", "FLATTEN"):
                if k in env:
                    print(f"    [{config}/{tile}] env {k}={env[k]}")
            print(f"    [{config}/{tile}] $ mflowgen run --design {MFLOWGEN_DIR / tile}; "
                  + "".join(f"make clean-{c}; " for c in filter(None, args.clean.split(",")))
                  + f"make -j{args.parallel_jobs} " + " ".join(f"post-synth-power-{v}" for v, _ in variants))
            status[(config, tile)] = ("DRY", 0.0, "")
            return
        ws.mkdir(parents=True, exist_ok=True)
        spec_file = ws / "spec_config.json"
        spec_text = json.dumps(man["spec_config"], indent=2, sort_keys=True)
        if not spec_file.exists() or spec_file.read_text() != spec_text:
            spec_file.write_text(spec_text)
        if man.get("pond_spec") is not None:
            pond_file = ws / "pond_spec.json"
            pond_text = json.dumps(man["pond_spec"], indent=2, sort_keys=True)
            if not pond_file.exists() or pond_file.read_text() != pond_text:
                pond_file.write_text(pond_text)
        json.dump({"config": config, "tile": tile, "variants": {v: str(d / config) for v, d in variants},
                   "mode": man["mode"], "clock_mhz": args.clock_mhz, "garnet": git_rev(GARNET_DIR),
                   "argv": sys.argv,
                   "started": time.strftime("%Y-%m-%d %H:%M:%S")},
                  open(ws / "run_meta.json", "w"), indent=1)
        env = tile_env(tile, ws, man, variants, config, args)
        sh(["mflowgen", "run", "--design", str(MFLOWGEN_DIR / tile)], ws, env, ws / "mflowgen_run.log")
        jobs = [f"-j{args.parallel_jobs}"] if args.parallel_jobs > 1 else []
        for step in filter(None, args.clean.split(",")):
            sh(["make", f"clean-{step}"], ws, env, ws / f"clean_{step}.log")
        sh(["make", *jobs, *[f"post-synth-power-{v}" for v, _ in variants]], ws, env, ws / "make.log")
        status[(config, tile)] = ("PASS", time.time() - t0, "")
    except Exception as e:  # noqa: BLE001 -- one tile's failure must not stop the other
        status[(config, tile)] = ("FAIL", time.time() - t0, str(e))
        print(f"    [{config}/{tile}] FAIL: {e}", flush=True)


def git_rev(path):
    r = subprocess.run(["git", "-C", str(path), "describe", "--always", "--dirty"],
                       capture_output=True, text=True)
    return r.stdout.strip() or None


# --------------------------------------------------------------- report ----

NUM = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"


def hier_total(path, top):
    """(internal, switching, leakage, total) W of the tile's own row."""
    for line in Path(path).read_text(errors="replace").splitlines():
        w = line.split()
        if w[:1] == [top]:
            nums = [float(x) for x in w[1:] if re.fullmatch(NUM, x)]
            if len(nums) >= 4:
                return tuple(nums[:4])
    return None


def cell_power(path, ref_re):
    """Total W of leaf cells whose reference name matches ref_re (report_power
    -hierarchy -leaf: `<inst> (<ref>)  int switch leak total %`), and their count."""
    total, n = 0.0, 0
    rx = re.compile(ref_re)
    for m in re.finditer(r"^\s*\S+\s+\((\S+)\)\s+(" + NUM + r")\s+(" + NUM + r")\s+(" + NUM + r")\s+(" + NUM + r")",
                         Path(path).read_text(errors="replace"), re.M):
        if rx.search(m.group(1)):
            total += float(m.group(5))
            n += 1
    return total, n


TIME = {"FS": 1e-15, "PS": 1e-12, "NS": 1e-9, "US": 1e-6, "MS": 1e-3, "S": 1.0}


def replay_window(log_text):
    """Seconds from the last stall release (stop stall_toggle: ...stall = 0,
    where common/testbench/cmd.tcl starts the SAIF) to $finish."""
    starts = re.findall(r"(\d+)\s*(FS|PS|NS|US|MS)\s*\+\s*\d+\s*\(stop stall_toggle:\s*\S+\s*=\s*0\)", log_text)
    end = re.search(r"Simulation complete via \$finish\(\d\) at time (\d+)\s*(FS|PS|NS|US|MS)", log_text)
    if not end:
        return None
    t1 = int(end.group(1)) * TIME[end.group(2)]
    t0 = int(starts[-1][0]) * TIME[starts[-1][1]] if starts else 0.0
    return t1 - t0


def tile_roles(bundle):
    """{Tile_Xxx_Yyy: (design, role)} from a bundle's tiles lists."""
    out = {}
    for design in TILES:
        f = Path(bundle) / f"tiles_{design}.list"
        if not f.is_file():
            continue
        for line in f.read_text().splitlines():
            fields = line.strip().split(",")
            if len(fields) >= 3:
                tile = f"Tile_X{fields[-2]}_Y{fields[-1]}"
                name = ",".join(fields[:-2])
                out[tile] = (design, name if name in ("route", "idle") else "placed")
    return out


def tile_rows(out_dir, sram_re):
    rows = []
    for meta_path in sorted(Path(out_dir).glob("*/*/run_meta.json")):
        meta = json.load(open(meta_path))
        ws, tile_design = meta_path.parent, meta["tile"]
        for v, bundle in meta["variants"].items():
            roles = tile_roles(bundle)
            steps = sorted(ws.glob(f"*-post-synth-power-{v}"))
            if not steps:
                continue
            reports = steps[-1] / "outputs" / "reports"
            for hier in sorted(reports.glob("Tile_X*.hier")):
                tile = hier.stem
                p = hier_total(hier, tile_design)
                cell = reports / f"{tile}.cell"
                sram, n_sram = cell_power(cell, sram_re) if cell.is_file() else (None, 0)
                rj = reports / f"{tile}.replay.json"
                rep = json.load(open(rj)) if rj.is_file() else {}
                logs = sorted(steps[-1].glob(f"{tile}/*-cadence-xcelium-sim/xrun.log")) or \
                    sorted(steps[-1].glob(f"{tile}/*-cadence-xcelium-sim/mflowgen-run.log"))
                window = replay_window(logs[-1].read_text(errors="replace")) if logs else None
                design, role = roles.get(tile, (tile_design, "placed"))
                rows.append(dict(
                    config=meta["config"], variant=v, design=tile_design, tile=tile, role=role,
                    internal_W=p and p[0], switching_W=p and p[1], leakage_W=p and p[2], total_W=p and p[3],
                    sram_W=sram if n_sram else None, sram_cells=n_sram,
                    window_s=window, energy_J=(p[3] * window) if p and window else None,
                    replay_exact=(not rep.get("problems")) if rep else None))
    return rows


def summarize(rows, out_dir):
    # variants in the run's --variants order (the first is the reference)
    meta = {}
    for mp in sorted(Path(out_dir).glob("*/*/run_meta.json")):
        m = json.load(open(mp))
        meta.setdefault(m["config"], m)
    order = {c: [v for v in m["variants"] if any(r["config"] == c and r["variant"] == v for r in rows)]
             for c, m in meta.items()}
    out = []
    for config, vs in order.items():
        ref = None
        for v in vs:
            rs = [r for r in rows if r["config"] == config and r["variant"] == v]
            bundle = Path(meta[config]["variants"][v])
            man = json.load(open(bundle / "manifest.json")) if (bundle / "manifest.json").is_file() else {}
            array = man.get("array_tiles") or {}
            s = dict(config=config, variant=v, app=man.get("app"),
                     tiles_replayed=len(rs), tiles_exact=sum(bool(r["replay_exact"]) for r in rs))
            app_w = app_j = sram = 0.0
            have_sram = False
            for d in TILES:
                for role in ("placed", "route"):
                    sel = [r for r in rs if r["design"] == d and r["role"] == role and r["total_W"] is not None]
                    s[f"{d}_{role}_n"] = len(sel)
                    s[f"{d}_{role}_W"] = sum(r["total_W"] for r in sel)
                    app_w += s[f"{d}_{role}_W"]
                    app_j += sum(r["energy_J"] or 0.0 for r in sel)
                    for r in sel:
                        if r["sram_W"] is not None:
                            sram += r["sram_W"]
                            have_sram = True
            s["app_W"], s["app_J"] = app_w, app_j
            s["sram_W"] = sram if have_sram else None
            windows = [r["window_s"] for r in rs if r["window_s"]]
            s["window_s"] = max(windows) if windows else None
            # idle tiles: one replayed per type, times the tiles the app leaves untouched
            idle_w, idle_known = 0.0, bool(array)
            for d in TILES:
                idle = [r for r in rs if r["design"] == d and r["role"] == "idle" and r["total_W"] is not None]
                used = s[f"{d}_placed_n"] + s[f"{d}_route_n"]
                n_idle = max(0, array.get(d, 0) - used) if array else None
                s[f"{d}_idle_n"] = n_idle
                s[f"{d}_idle_tile_W"] = idle[0]["total_W"] if idle else None
                if idle and n_idle is not None:
                    idle_w += idle[0]["total_W"] * n_idle
                elif n_idle:
                    idle_known = False
            s["idle_W"] = idle_w if idle_known else None
            s["array_W"] = app_w + idle_w if idle_known else None
            s["array_J"] = s["array_W"] * s["window_s"] if idle_known and s["window_s"] else None
            if ref is None:
                ref = s
            for k in ("app_W", "app_J", "sram_W", "array_W", "array_J", "window_s"):
                a, b = s.get(k), ref.get(k)
                s[f"d_{k}_pct"] = (100.0 * (a - b) / b) if a is not None and b else None
            out.append(s)
    return out


def write_csv(path, rows):
    if not rows:
        return
    keys = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()})


def report(args):
    out_dir = Path(args.out_dir).resolve()
    rows = tile_rows(out_dir, args.sram_cell_re)
    summary = summarize(rows, out_dir)
    write_csv(out_dir / "cgra_power_tiles.csv", rows)
    write_csv(out_dir / "cgra_power.csv", summary)
    if not summary:
        print("no per-tile reports yet")
        return
    fmt = lambda v, s=1e3: "-" if v is None else f"{v * s:.3f}"
    pct = lambda v: "" if v is None else f" ({v:+.1f}%)"
    print(f"\n{'config / variant':42s} {'tiles':>9s} {'app mW':>16s} {'SRAM mW':>16s} "
          f"{'array mW':>18s} {'app uJ/run':>18s}")
    for s in summary:
        print(f"{s['config'] + ' / ' + s['variant']:42s} {s['tiles_exact']:>3}/{s['tiles_replayed']:<3} exact "
              f"{fmt(s['app_W']) + pct(s['d_app_W_pct']):>16s} {fmt(s['sram_W']) + pct(s['d_sram_W_pct']):>16s} "
              f"{fmt(s['array_W']) + pct(s['d_array_W_pct']):>18s} "
              f"{fmt(s['app_J'], 1e6) + pct(s['d_app_J_pct']):>18s}")
    print(f"\nwrote {out_dir / 'cgra_power.csv'} and cgra_power_tiles.csv")


def zip_results(args):
    out_dir = Path(args.out_dir).resolve()
    path = Path(f"{out_dir}_{socket.gethostname().split('.')[0]}_{time.strftime('%Y%m%d-%H%M%S')}.zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out_dir.glob("*.csv")):
            z.write(f, f.relative_to(out_dir.parent))
        for ws in sorted(p.parent for p in out_dir.glob("*/*/run_meta.json")):
            for f in [*ws.glob("*.json"), *ws.glob("*.log"),
                      *ws.glob("*-post-synth-power-*/outputs/reports/*"),
                      *ws.glob("*-application-*/outputs/manifest.json"),
                      *ws.glob("*-application-*/outputs/tiles_*.list"),
                      *ws.glob("*-cadence-genus-synthesis/reports/*area*"),
                      *ws.glob("*-post-synth-power-*/Tile_X*/*-cadence-xcelium-sim/xrun.log")]:
                if f.is_file():
                    z.write(f, f.relative_to(out_dir.parent))
    print(f"zip: {path} ({path.stat().st_size / 1e6:.1f} MB)")


# ----------------------------------------------------------------- main ----

def main(argv=None):
    args = parse_args(argv)
    out_dir = Path(args.out_dir).resolve()
    if not args.report_only:
        if GARNET_DIR in out_dir.parents or out_dir == GARNET_DIR:
            raise SystemExit("*** keep --out-dir outside the garnet checkout (the rtl step docker-cps it)")
        variants = parse_variants(args.variants)
        if len(variants) < 1:
            raise SystemExit("*** give --variants NAME=DIR[,NAME=DIR...]")
        if not args.dry_run and shutil.which("mflowgen") is None:
            raise SystemExit("*** mflowgen not on PATH")
        tiles = [t for t in args.tiles.split(",") if t]
        bad = [t for t in tiles if t not in TILES]
        if bad:
            raise SystemExit(f"*** --tiles: unknown {bad}")
        configs = configs_of(variants, args.config)
        jobs = []
        for config in configs:
            man = load_manifests(variants, config)[variants[0][0]]
            print(f"{config}: mode {man['mode']}, app {man.get('app')}, variants "
                  + ", ".join(v for v, _ in variants), flush=True)
            jobs += [(t, config, man) for t in tiles]
        status, sem = {}, threading.Semaphore(max(1, args.tile_jobs))

        def run(job):
            with sem:
                build_tile(*job[:2], variants, job[2], args, status)
        threads = [threading.Thread(target=run, args=(j,)) for j in jobs]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        for (config, tile), (st, dur, note) in sorted(status.items()):
            print(f"  {st}  {config}/{tile}  {dur / 60:.0f} min" + (f"  ({note.splitlines()[0]})" if note else ""))
        if args.dry_run:
            return 0
    report(args)
    if args.zip:
        zip_results(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
