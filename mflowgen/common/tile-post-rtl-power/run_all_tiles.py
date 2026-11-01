"""Per-tile app-driven power: run this level's per-tile sub-graph (./run.sh,
which makes the tile's xcelium sim + ptpx and copies its power.hier to
outputs/reports/<tile>.hier) for every placed tile of design_name, then check
that each tile's simulation replayed the recorded app run exactly.

The tile testbench (common/testbench) prints one line per output port and
cycle that differs from the recording ("cycle N: <port>: got X, expected Y",
X included). A replay that differs means the tile is not the one the app ran
on (stale app bundle, other RTL), so its power describes some other activity.
With a bundle the testbench holds reset until the recording's first reset and
checks from that cycle on (it prints "replay: ... before cycle N"; checked_from),
and prints the app start (first flush after it; app_start). Before the app
starts, an X/Z output where the recording has a known value is state without
reset, which the recording's simulator zero-initialized (gate level: the MEM
output port's PISO registers until the app writes them): counted as
pre_app_x, not as a mismatch. After it, an output port whose every mismatch
is X/Z where the recording holds one known value is the same reset-less
state, not yet written or never written by the app (gf12 flops are X until
written; e.g. a switch-box output the app does not use, or a MEM output
before the app's first write to it): counted per port as idle_x
(idle_x_ports), not as mismatches. A port with any known-value mismatch, or
X where the recording changes, fails with all its mismatches.
Per tile: outputs/reports/<tile>.replay.json (+ <tile>.mismatches.txt, the
first mismatch lines); all tiles: outputs/reports/replay_summary.txt.

make re-runs a failed step in its build dir: a tile an earlier run replayed
to the end (its power report and finished sim log are kept) is then only
checked again (rechecked), and a tile that had not finished starts over.
cgra_app_power.py copies the current script into such a step first.

Parameter replay_check: "fail" exits non-zero after all tiles ran (reports
are still written) if any tile mismatched, did not finish its sim, or has no
power report; "warn" only prints; "auto" (default) = "fail" with an app bundle
(app_bundle set), else "warn" (the legacy stock-container app run was never
checked against the tile). Identical copy in
tile-post-{rtl,synth,pnr}-power (tests/test_app_bundle_guards checks that).
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

MISMATCH = re.compile(r"cycle\s+(\d+):\s*(\S+):\s+got\s+(\S+),\s+expected\s+(\S+)")
FINISHED = re.compile(r"Simulation complete via \$finish")
CHECKED_FROM = re.compile(r"replay: reset held and outputs not checked before cycle (\d+)")
APP_START = re.compile(r"replay: app starts at cycle (\d+)")
XZ = re.compile(r"[xXzZ]")
MAX_EXAMPLES = 5
MAX_SAVED_LINES = 5000   # outputs/reports/<tile>.mismatches.txt (the sweep zips reports/*)
# A replayed tile's sub-workspace keeps only these once its reports are saved
# (env REPLAY_KEEP_TILES=True keeps all of it): its copies of the netlist and
# test vectors, its simulation snapshot and SAIF are 100s of MB per tile for a
# long app, and a 16x16 cgra_app_power run filled the build disk with them.
KEEP_FILES = ("mflowgen-run.log", "xrun.log")


def tile_ids(design):
    ids = []
    with open(f"./inputs/tiles_{design}.list") as f:
        for line in f:
            fields = line.strip().split(",")
            if len(fields) >= 2:
                ids.append(f"Tile_X{fields[-2]}_Y{fields[-1]}")
    return ids


def sim_log(tile_dir):
    """The tile sub-graph's xcelium log (xrun.log, else the step's run log)."""
    for name in ("xrun.log", "mflowgen-run.log"):
        logs = sorted(glob.glob(os.path.join(tile_dir, "*-cadence-xcelium-sim", name)))
        if logs:
            return logs[-1]
    return None


def idle_x_ports(found):
    """{port: {'lines', 'expected', 'first_cycle', 'last_cycle'}} of the ports
    whose every mismatch in found [(cycle, port, got, exp)] is X/Z where the
    recording holds one known value."""
    by_port = {}
    for cycle, port, got, exp in found:
        by_port.setdefault(port, []).append((cycle, got, exp))
    out = {}
    for port, ms in by_port.items():
        exps = {exp for _, _, exp in ms}
        if len(exps) == 1 and not XZ.search(ms[0][2]) and all(XZ.search(got) for _, got, _ in ms):
            cycles = [cycle for cycle, _, _ in ms]
            out[port] = {"lines": len(ms), "expected": ms[0][2],
                         "first_cycle": min(cycles), "last_cycle": max(cycles)}
    return out


def replay_result(log_text):
    """{'finished', 'checked_from', 'app_start', 'pre_app_x', 'pre_app_x_examples',
    'idle_x', 'idle_x_ports', 'mismatches', 'x_mismatches' (got has x/z),
    'first_cycle', 'last_cycle', 'ports': {port: n}, 'examples', 'lines'} of a
    tile sim log."""
    checked_from, app_start = CHECKED_FROM.search(log_text), APP_START.search(log_text)
    app_start = int(app_start.group(1)) if app_start else None
    pre_app_x, pre_app_examples, found = 0, [], []
    for m in MISMATCH.finditer(log_text):
        cycle, port, got, exp = int(m.group(1)), m.group(2), m.group(3), m.group(4)
        if app_start is not None and cycle < app_start and XZ.search(got) and not XZ.search(exp):
            pre_app_x += 1
            if len(pre_app_examples) < MAX_EXAMPLES:
                pre_app_examples.append(f"cycle {cycle}: {port}: got {got}, expected {exp}")
            continue
        found.append((cycle, port, got, exp))
    idle = idle_x_ports(found)
    ports, examples, lines, n, nx, cycles = {}, [], [], 0, 0, []
    for cycle, port, got, exp in found:
        if port in idle:
            continue
        line = f"cycle {cycle}: {port}: got {got}, expected {exp}"
        n += 1
        nx += bool(XZ.search(got))
        cycles.append(cycle)
        ports[port] = ports.get(port, 0) + 1
        if len(examples) < MAX_EXAMPLES:
            examples.append(line)
        if len(lines) < MAX_SAVED_LINES:
            lines.append(line)
    return {"finished": bool(FINISHED.search(log_text)),
            "checked_from": int(checked_from.group(1)) if checked_from else None,
            "app_start": app_start, "pre_app_x": pre_app_x, "pre_app_x_examples": pre_app_examples,
            "idle_x": sum(p["lines"] for p in idle.values()), "idle_x_ports": idle,
            "mismatches": n, "x_mismatches": nx,
            "first_cycle": min(cycles) if cycles else None, "last_cycle": max(cycles) if cycles else None,
            "ports": ports, "examples": examples, "lines": lines}


def problems_of(res):
    out = []
    if not res["report"]:
        out.append("no power report")
    if res["sim_log"] is None:
        out.append("no sim log")
    elif not res["finished"]:
        out.append("sim did not reach $finish")
    if res["mismatches"]:
        out.append(f"{res['mismatches']} replay mismatches ({res['x_mismatches']} with x/z, cycles "
                   f"{res['first_cycle']}-{res['last_cycle']}; "
                   f"{', '.join(f'{p} {c}' for p, c in sorted(res['ports'].items()))})")
    return out


def notes_of(res):
    """The summary line's note on the X outputs not counted as mismatches."""
    notes = []
    if res["pre_app_x"]:
        notes.append(f"{res['pre_app_x']} X outputs before the app start at cycle {res['app_start']} not counted")
    if res["idle_x"]:
        notes.append(f"{res['idle_x']} X outputs where the recording holds a constant not counted: "
                     + ", ".join(f"{p} {v['lines']} (cycles {v['first_cycle']}-{v['last_cycle']}, "
                                 f"recorded {v['expected']})" for p, v in sorted(res["idle_x_ports"].items())))
    return f" ({'; '.join(notes)})" if notes else ""


def check_tile(tile, run_rc, rechecked=False):
    log = sim_log(tile)
    res = replay_result(open(log, errors="replace").read()) if log else \
        {"finished": False, "checked_from": None, "app_start": None, "pre_app_x": 0, "pre_app_x_examples": [],
         "idle_x": 0, "idle_x_ports": {}, "mismatches": None, "x_mismatches": None, "first_cycle": None,
         "last_cycle": None, "ports": {}, "examples": [], "lines": []}
    res.update(tile=tile, sim_log=log, run_rc=run_rc, rechecked=rechecked,
               report=os.path.isfile(f"outputs/reports/{tile}.hier"))
    res["problems"] = problems_of(res)
    lines = res.pop("lines")
    saved = f"outputs/reports/{tile}.mismatches.txt"
    if lines:
        with open(saved, "w") as f:
            f.write("\n".join(lines) + "\n")
    elif os.path.exists(saved):   # an earlier check's
        os.unlink(saved)
    with open(f"outputs/reports/{tile}.replay.json", "w") as f:
        json.dump(res, f, indent=1)
    return res


def prune_tile(tile):
    """Delete everything in the tile's sub-workspace but its logs (KEEP_FILES).
    Symlinks are removed, never followed."""
    for root, dirs, files in os.walk(tile, topdown=False):
        for f in files:
            if f not in KEEP_FILES or os.path.islink(os.path.join(root, f)):
                os.unlink(os.path.join(root, f))
        for d in dirs:
            p = os.path.join(root, d)
            if os.path.islink(p):
                os.unlink(p)
            elif not os.listdir(p):
                os.rmdir(p)


def replayed_before(tile):
    """True if an earlier run of this step replayed the tile to the end: its
    power report and its finished sim log (prune_tile keeps it) are there."""
    log = sim_log(tile)
    return (log is not None and os.path.isfile(f"outputs/reports/{tile}.hier")
            and bool(FINISHED.search(open(log, errors="replace").read())))


def replay_tile(tile):
    """Run the tile's sub-graph (./run.sh), check its replay, then prune it.
    A tile an earlier run of this step replayed to the end is only checked
    again; one it left unfinished starts over in a fresh sub-workspace.
    Tiles are independent (own sub-workspace and report files), so main() runs
    up to REPLAY_TILE_JOBS of them at once; their tools then queue for licenses
    (xrun -licqueue in run_sim.sh, SNPSLMD_QUEUE for PrimeTime)."""
    if replayed_before(tile):
        print(f"{tile}: replayed by an earlier run of this step; checking its kept sim log again", flush=True)
        return check_tile(tile, None, rechecked=True)
    if os.path.isdir(tile) and not os.path.islink(tile):
        shutil.rmtree(tile)
    env = dict(os.environ, tile_id=tile, SNPSLMD_QUEUE="true")
    rc = subprocess.run(["./run.sh"], env=env).returncode
    res = check_tile(tile, rc)
    if os.environ.get("REPLAY_KEEP_TILES", "").lower() not in ("1", "true"):
        prune_tile(tile)
    return res


def main():
    design = os.environ.get("design_name")
    mode = os.environ.get("replay_check") or "auto"
    if mode == "auto":
        mode = "fail" if os.environ.get("app_bundle") else "warn"
    os.makedirs("outputs/reports", exist_ok=True)
    jobs = max(1, int(os.environ.get("REPLAY_TILE_JOBS") or 1))
    with ThreadPoolExecutor(jobs) as pool:   # map keeps the tile order
        results = list(pool.map(replay_tile, tile_ids(design)))

    lines = [f"{r['tile']}: {'; '.join(r['problems']) or 'OK'}" + notes_of(r) for r in results]
    bad = [r for r in results if r["problems"]]
    lines.append(f"{design}: {len(results) - len(bad)}/{len(results)} tiles replayed exactly")
    with open("outputs/reports/replay_summary.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    for r in bad:
        for e in r["examples"]:
            print(f"  {r['tile']}: {e}")
    if bad:
        print(f"*** {'ERROR' if mode == 'fail' else 'WARNING'}: {len(bad)} {design} tile(s) did not "
              f"replay the app run exactly; their power is not the app's (replay_check={mode})",
              file=sys.stderr)
        if mode == "fail":
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
