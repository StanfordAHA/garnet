#!/usr/bin/env python3
"""Record an app bundle: one Halide app run on a lake-spec CGRA, for the
Tile_MemCore / Tile_PE power steps (common/application app_bundle param,
sweep_specs.py --app-bundle-dir). See mflowgen/CLAUDE.md "App bundles".

Runs where the spec toolchain lives (an aha tree: Halide, clockwork with lake
collateral, garnet, lake), with the same flags and per-stage env as aha's
ready-valid regression:

  collateral  lake.utils.spec_config_to_collateral (+ pond_collateral)
  halide/map  aha halide / aha map --collateral [--pond-collateral]
              (RV: DENSE_READY_VALID=1 PIPELINED=0 MATCH_BRANCH_DELAY=0)
  garnet      garnet.py --verilog --lake-spec-config/-mode --use-non-split-fifos
              --use_sim_sram (no ready-valid env; it never shapes RTL)
  pnr         aha pnr (RV: DENSE_READY_VALID=1 EXHAUSTIVE_PIPE=1)
  test        aha test with DUMP_ARGS = probes of every placed MEM/PE tile's
              ports (-> run.vcd) and of each MEM tile's lake controller
              (-> core.vcd); aha test's own gold compare must pass

and writes to --out:
  run.vcd, tiles_Tile_MemCore.list, tiles_Tile_PE.list, tile_ports.json,
  manifest.json            what the application step copies
  core.vcd, core_ports.json  MEM tiles' lakespec controller ports (standalone
                           lakespec replay)
  garnet.v.gz, design.place, *.bs, logs/   provenance

  python3 gen_app_bundle.py --config fw4_dw16_sc4096_sp_in2_out2_vc2_rv \\
      --app tests/conv_3_3 --bundle-dir bundles

--config takes a sweep_specs.py config name (spec + mode, as the sweep
writes them) and names the bundle <bundle-dir>/<config>, the layout
sweep_specs --app-bundle-dir expects; --spec/--mode/--out set them by hand.
Needs xrun on PATH (module load xcelium), aha's venv, and a garnet whose
tests/test_app/Makefile takes DUMP_ARGS from the environment.

garnet.py --verilog rewrites GLB/GLC headers under $GARNET_HOME, which every
`aha test` on that tree simulates against: run in a private aha tree
(--aha-dir, `aha --dir`) when other users share the default one.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

RV_MAP_ENV = {"DENSE_READY_VALID": "1", "PIPELINED": "0", "MATCH_BRANCH_DELAY": "0"}
RV_PNR_ENV = {"DENSE_READY_VALID": "1", "EXHAUSTIVE_PIPE": "1"}
RV_VARS = ("DENSE_READY_VALID", "PIPELINED", "MATCH_BRANCH_DELAY", "EXHAUSTIVE_PIPE")
SCOPE = "top.dut.Interconnect_inst0"
TILE_DESIGNS = {"m": "Tile_MemCore", "p": "Tile_PE"}
# The MEM tile's lake controller (config_memory + port_<i>_f_): the outermost
# match on the Tile_MemCore hierarchy -- lakespec_flat (static spec) or
# lakespec_mem_flat (RV spec).
CORE_MODULE_RE = re.compile(r"^lakespec(_mem)?(_flat)?$")
STEPS = ("collateral", "halide", "map", "garnet", "pnr", "test", "package")


def sweep_config(name):
    """(spec kwargs, mode) of a sweep_specs.py config name, from its spec sets."""
    path = Path(__file__).resolve().parents[2] / "sweep_specs.py"
    spec = importlib.util.spec_from_file_location("sweep_specs", path)
    ss = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ss)
    for specs in ss.SPEC_SETS.values():
        for s in specs:
            for mode in ([s["runtime_mode"]] if s.get("runtime_mode") else ss.RUNTIME_MODES):
                cfg = dict(s, runtime_mode=mode)
                if ss._config_name(cfg) == name and not ss._unsupported_reason(s, mode):
                    return ss._spec_kwargs(cfg), mode
    sys.exit(f"*** no config {name} in sweep_specs.py's spec sets (sweep_specs.py --list)")


def log(msg):
    print(f"=== [{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(name, cmd, env, cwd, logs, timeout=None):
    """Run cmd (own process group, killed on timeout) -> logs/<name>.log; exit
    with the log tail on failure."""
    path = logs / f"{name}.log"
    log(f"{name}: {' '.join(str(c) for c in cmd)}  (log {path})")
    with open(path, "w") as f:
        p = subprocess.Popen([str(c) for c in cmd], cwd=str(cwd), env=env, stdout=f,
                             stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGTERM)
            time.sleep(5)
            os.killpg(p.pid, signal.SIGKILL)
            rc = "timeout"
    if rc != 0:
        tail = path.read_text(errors="replace").splitlines()[-30:]
        sys.exit(f"*** {name} FAILED (rc={rc}); last lines of {path}:\n" + "\n".join(tail))
    return path


# ---------------------------------------------------------------- garnet.v ---

def verilog_modules(src):
    """{module: (header text, [(type, instance), ...])} for a garnet.v. Instance
    lines are `Type inst (` (parameterized `Type #(...) inst (` lines are
    primitives and skipped)."""
    mods = {}
    for m in re.finditer(r"^module (\w+)\s*(.*?)^endmodule", src, re.M | re.S):
        body = m.group(2)
        header = body[:body.find(");") + 1]
        insts = re.findall(r"^\s*(\w+)\s+(\w+)\s*\($", body, re.M)
        mods[m.group(1)] = (header, insts)
    return mods


def module_ports(header):
    """[[name, width], ...] per direction from an ANSI port header
    (`input logic [15:0] x`, `input logic [0:0] [16:0] x`, `output x`)."""
    ports = {"inputs": [], "outputs": []}
    for d, dims, name in re.findall(
            r"(input|output)\s+(?:wire\s+|logic\s+|reg\s+)?((?:\[\d+:\d+\]\s*)*)([A-Za-z_]\w*)\s*[,)]",
            header):
        width = 1
        for hi, lo in re.findall(r"\[(\d+):(\d+)\]", dims):
            width *= abs(int(hi) - int(lo)) + 1
        ports["inputs" if d == "input" else "outputs"].append([name, width])
    return ports


def find_instance_path(mods, root, pattern):
    """Breadth-first: (dotted instance path, module) of the first module under
    root whose name matches pattern, or (None, None)."""
    frontier = [(root, ())]
    while frontier:
        nxt = []
        for mod, path in frontier:
            for typ, inst in mods.get(mod, ("", []))[1]:
                if typ not in mods:
                    continue
                if pattern.match(typ):
                    return ".".join(path + (inst,)), typ
                nxt.append((typ, path + (inst,)))
        frontier = nxt
    return None, None


# ------------------------------------------------------------------ main ----

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", default=None,
                   help="sweep_specs.py config name: sets --spec/--mode and names the bundle")
    p.add_argument("--bundle-dir", default=None,
                   help="with --config: write the bundle to <bundle-dir>/<config>")
    p.add_argument("--spec", default=None,
                   help="lake spec JSON (build_spec kwargs; the sweep's spec_config.json)")
    p.add_argument("--mode", choices=("static", "rv"), default=None)
    p.add_argument("--app", default="tests/conv_3_3",
                   help="app under Halide-to-Hardware/apps/hardware_benchmarks")
    p.add_argument("--out", default=None, help="bundle directory")
    p.add_argument("--width", type=int, default=16)
    p.add_argument("--height", type=int, default=16)
    p.add_argument("--glb-tile-mem-size", type=int, default=128)
    p.add_argument("--pond-spec", default=None,
                   help="PE-tile pond spec JSON (--lake-pond-spec-config + pond collateral); "
                        "default: garnet's default pond, clockwork's built-in pond preset")
    p.add_argument("--aha-dir", default=os.environ.get("AHA_DIR", "/aha"),
                   help="aha tree (`aha --dir`); its garnet is GARNET_HOME (default /aha)")
    p.add_argument("--env", action="append", default=[], metavar="KEY=VAL",
                   help="extra env for halide/map/pnr/test (e.g. HL_TARGET=..., EXT=mat)")
    p.add_argument("--pre-pnr-hook", action="append", default=[], metavar="SCRIPT",
                   help="python SCRIPT <app>/bin, run between map and pnr")
    p.add_argument("--skip-to", choices=STEPS, default="collateral",
                   help="resume: reuse the earlier steps' results (same --out)")
    p.add_argument("--test-timeout", type=int, default=5400,
                   help="seconds before the sim is killed (the tb waits 6M cycles per interrupt)")
    args = p.parse_args()
    if args.config:
        if args.spec or args.mode:
            p.error("--config sets the spec and mode; drop --spec/--mode")
        cfg_spec, args.mode = sweep_config(args.config)
        if not args.out:
            if not args.bundle_dir:
                p.error("--config needs --bundle-dir or --out")
            args.out = str(Path(args.bundle_dir) / args.config)
    elif not (args.spec and args.mode and args.out):
        p.error("give --config, or --spec, --mode and --out")

    aha_dir = Path(args.aha_dir).resolve()
    garnet = aha_dir / "garnet"
    app_dir = aha_dir / "Halide-to-Hardware/apps/hardware_benchmarks" / args.app
    out = Path(args.out).resolve()
    work, logs = out / "work", out / "logs"
    for d in (work, logs):
        d.mkdir(parents=True, exist_ok=True)
    skip = STEPS.index(args.skip_to)
    if not app_dir.is_dir():
        sys.exit(f"*** no app {app_dir}")
    if not shutil.which("xrun"):
        sys.exit("*** xrun not on PATH (source /cad/modules/tcl/init/bash; module load base xcelium)")
    if "DUMP_ARGS ?=" not in (garnet / "tests/test_app/Makefile").read_text():
        sys.exit(f"*** {garnet}/tests/test_app/Makefile ignores DUMP_ARGS from the env "
                 "(needs garnet with the `DUMP_ARGS ?=` change)")

    spec = work / "spec_config.json"
    if skip == 0:
        if args.config:
            spec.write_text(json.dumps(cfg_spec, indent=2, sort_keys=True))
        else:
            shutil.copy(args.spec, spec)
    rv = args.mode == "rv"
    coll = work / "lake_collateral.json"
    pond_coll = work / "pond_collateral.json" if args.pond_spec else None
    pond_spec = work / "pond_spec.json" if args.pond_spec else None

    base = dict(os.environ)
    for k in RV_VARS:
        base.pop(k, None)
    base.update(GARNET_HOME=str(garnet), TOOL="XCELIUM")
    for kv in args.env:
        k, _, v = kv.partition("=")
        base[k] = v
    spec_env = dict(base, LAKE_SPEC_CONFIG=str(spec), LAKE_SPEC_MODE=args.mode,
                    USE_NON_SPLIT_FIFOS="1")
    if pond_spec:
        spec_env["LAKE_POND_SPEC_CONFIG"] = str(pond_spec)
    aha = ["aha"] + (["--dir", str(aha_dir)] if aha_dir != Path("/aha") else [])
    coll_flags = ["--collateral", str(coll)] + (["--pond-collateral", str(pond_coll)] if pond_coll else [])
    garnet_flags = ["--width", args.width, "--height", args.height, "--use_sim_sram",
                    "--glb_tile_mem_size", args.glb_tile_mem_size,
                    "--lake-spec-config", spec, "--lake-spec-mode", args.mode,
                    "--use-non-split-fifos"]
    if pond_spec:
        garnet_flags += ["--lake-pond-spec-config", pond_spec]

    # 1. collateral
    if skip <= 0:
        if pond_spec:
            shutil.copy(args.pond_spec, pond_spec)
        run("collateral", [sys.executable, "-m", "lake.utils.spec_config_to_collateral",
                           "--spec", spec, "-o", coll], base, work, logs)
        if pond_coll:
            run("pond_collateral", [sys.executable, "-m", "lake.utils.pond_collateral",
                                    "--pond-spec", pond_spec, "-o", pond_coll] + (["--rv"] if rv else []),
                base, work, logs)

    # 2-3. halide + map (ready-valid env reaches clockwork in rv mode)
    map_env = dict(base, **(RV_MAP_ENV if rv else {}))
    if skip <= 1:
        subprocess.run(["make", "clean"], cwd=app_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        run("halide", aha + ["halide", args.app] + coll_flags, map_env, aha_dir, logs)
    if skip <= 2:
        run("map", aha + ["map", args.app] + coll_flags, map_env, aha_dir, logs)

    # 4. garnet.v (kratos/coreir segfault intermittently: retry)
    gv = garnet / "garnet.v"
    if skip <= 3:
        for attempt in range(3):
            path = logs / "garnet.log"
            r = subprocess.run([sys.executable, "garnet.py", "--verilog"] + [str(f) for f in garnet_flags],
                               cwd=garnet, env=spec_env, stdout=open(path, "w"), stderr=subprocess.STDOUT)
            if r.returncode == 0 or "garnet.py DONE" in path.read_text(errors="replace"):
                break
            shutil.copy(path, logs / f"garnet.attempt{attempt}.log")
            log(f"garnet attempt {attempt} rc={r.returncode}; retrying")
        else:
            sys.exit(f"*** garnet.py failed 3 times; see {logs}")
        glb = re.search(r"NUM_GLB_TILES = (\d+)",
                        (garnet / "global_buffer/header/global_buffer_param.svh").read_text())
        if not glb or int(glb.group(1)) != args.width // 2:
            sys.exit(f"*** GLB header NUM_GLB_TILES={glb and glb.group(1)} != {args.width // 2}: "
                     "another build rewrote this GARNET_HOME's headers")
    gv_md5 = md5(gv)
    log(f"garnet.v md5 {gv_md5}")

    # 5. pnr
    test_env = dict(spec_env, LAKE_COLLATERAL_JSON_MEM=str(coll), **(RV_PNR_ENV if rv else {}))
    if pond_coll:
        test_env["LAKE_COLLATERAL_JSON_REGFILE"] = str(pond_coll)
    if skip <= 4:
        for i, hook in enumerate(args.pre_pnr_hook):
            run(f"hook{i}", [sys.executable, hook, app_dir / "bin"], test_env, aha_dir, logs)
        run("pnr", aha + ["pnr", args.app] + [str(f) for f in garnet_flags], test_env, aha_dir, logs)

    # 6. sim with the tile-port probes + aha test's gold compare
    tiles = {k: [] for k in TILE_DESIGNS}
    for line in (app_dir / "bin/design.place").read_text().splitlines()[2:]:
        w = line.split()
        if len(w) >= 4 and w[-1].startswith("#") and w[-1][1] in tiles:
            tiles[w[-1][1]].append((w[0], int(w[-3]), int(w[-2])))
    mods = verilog_modules(gv.read_text())
    core_path, core_mod = find_instance_path(mods, "Tile_MemCore", CORE_MODULE_RE)
    tcl = [f"database -open tiles -vcd -into {out}/run.vcd -default"]
    if core_path:
        tcl.append(f"database -open core -vcd -into {out}/core.vcd")
    for k in tiles:
        for _, x, y in tiles[k]:
            tile = f"{SCOPE}.Tile_X{x:02X}_Y{y:02X}"
            tcl.append(f"probe -create {tile} -depth 1 -ports -database tiles")
            if k == "m" and core_path:
                tcl.append(f"probe -create {tile}.{core_path} -depth 1 -ports -database core")
    tcl += ["run", "exit"]
    probe = work / "probe.tcl"
    probe.write_text("\n".join(tcl) + "\n")
    if skip <= 5:
        sim_env = dict(test_env, DUMP_ARGS=f"-input {probe}", WAVEFORM="0", SAIF="0")
        tlog = run("test", aha + ["test", args.app], sim_env, aha_dir, logs, timeout=args.test_timeout)
        if not re.search(r"comparison passed", tlog.read_text(errors="replace")):
            sys.exit(f"*** aha test printed no 'comparison passed' ({tlog}): no bundle")

    # 7. package
    for k, design in TILE_DESIGNS.items():
        with open(out / f"tiles_{design}.list", "w") as f:
            for name, x, y in tiles[k]:
                f.write(f"{name},{x:02X},{y:02X}\n")
    tile_ports = {d: module_ports(mods[d][0]) for d in TILE_DESIGNS.values() if d in mods}
    json.dump(tile_ports, open(out / "tile_ports.json", "w"), indent=1)
    if core_path:
        json.dump(dict(path=core_path, module=core_mod, **module_ports(mods[core_mod][0])),
                  open(out / "core_ports.json", "w"), indent=1)
    shutil.copy(app_dir / "bin/design.place", out)
    for bs in (app_dir / "bin").glob("*.bs"):
        shutil.copy(bs, out)
    with open(gv, "rb") as fi, gzip.open(out / "garnet.v.gz", "wb") as fo:
        shutil.copyfileobj(fi, fo)

    def git(d):
        """git describe of d if d is a checkout's top level (a plain copy would
        report the enclosing repo), else None."""
        top = subprocess.run(["git", "-C", str(d), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True).stdout.strip()
        if not top or Path(top).resolve() != Path(d).resolve():
            return None
        return subprocess.run(["git", "-C", str(d), "describe", "--always", "--dirty"],
                              capture_output=True, text=True).stdout.strip() or None
    lake_file = subprocess.run([sys.executable, "-c", "import lake; print(lake.__file__)"],
                               env=base, capture_output=True, text=True).stdout.strip()
    lake_root = Path(lake_file).resolve().parents[1] if lake_file else None
    origin = lake_root / "ORIGIN.txt" if lake_root else None
    cw_lib = aha_dir / "clockwork/lib/libclkwrk.so"
    manifest = {
        "app": args.app, "mode": args.mode, "width": args.width, "height": args.height,
        "scope": SCOPE, "clock": "{scope}.{tile}.clk",
        "spec_config": json.load(open(spec)),
        "pond_spec": json.load(open(pond_spec)) if pond_spec else None,
        "app_env": dict(kv.partition("=")[::2] for kv in args.env),
        "pre_pnr_hooks": args.pre_pnr_hook,
        "tiles": {TILE_DESIGNS[k]: len(v) for k, v in tiles.items()},
        "core": {"vcd": "core.vcd", "path": core_path, "module": core_mod} if core_path else None,
        "garnet_flags": [str(f) for f in garnet_flags],
        "garnet_v_md5": gv_md5,
        "config": args.config,
        "git": {r: git(aha_dir / r) for r in ("garnet", "clockwork", "Halide-to-Hardware")},
        "lake_import": lake_file,
        "lake_git": (origin.read_text().strip() if origin and origin.exists()
                     else git(lake_root) if lake_root else None),
        "clockwork_lib_md5": md5(cw_lib) if cw_lib.exists() else None,
        "run_vcd_bytes": (out / "run.vcd").stat().st_size,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "command": " ".join(sys.argv),
    }
    json.dump(manifest, open(out / "manifest.json", "w"), indent=1)
    log(f"BUNDLE OK: {out} ({manifest['tiles']}, run.vcd {manifest['run_vcd_bytes']} bytes)")


if __name__ == "__main__":
    main()
