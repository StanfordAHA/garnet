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
pre_app_x, not as a mismatch. Known-value mismatches and X after it fail.
Per tile: outputs/reports/<tile>.replay.json (+ <tile>.mismatches.txt, the
first mismatch lines); all tiles: outputs/reports/replay_summary.txt.

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
import subprocess
import sys

MISMATCH = re.compile(r"cycle\s+(\d+):\s*(\S+):\s+got\s+(\S+),\s+expected\s+(\S+)")
FINISHED = re.compile(r"Simulation complete via \$finish")
CHECKED_FROM = re.compile(r"replay: reset held and outputs not checked before cycle (\d+)")
APP_START = re.compile(r"replay: app starts at cycle (\d+)")
XZ = re.compile(r"[xXzZ]")
MAX_EXAMPLES = 5
MAX_SAVED_LINES = 5000   # outputs/reports/<tile>.mismatches.txt (the sweep zips reports/*)


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


def replay_result(log_text):
    """{'finished', 'checked_from', 'app_start', 'pre_app_x', 'pre_app_x_examples',
    'mismatches', 'x_mismatches' (got has x/z), 'first_cycle', 'last_cycle',
    'ports': {port: n}, 'examples', 'lines'} of a tile sim log."""
    checked_from, app_start = CHECKED_FROM.search(log_text), APP_START.search(log_text)
    app_start = int(app_start.group(1)) if app_start else None
    ports, examples, lines, n, nx, cycles = {}, [], [], 0, 0, []
    pre_app_x, pre_app_examples = 0, []
    for m in MISMATCH.finditer(log_text):
        cycle, port, got, exp = int(m.group(1)), m.group(2), m.group(3), m.group(4)
        line = f"cycle {cycle}: {port}: got {got}, expected {exp}"
        if app_start is not None and cycle < app_start and XZ.search(got) and not XZ.search(exp):
            pre_app_x += 1
            if len(pre_app_examples) < MAX_EXAMPLES:
                pre_app_examples.append(line)
            continue
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


def check_tile(tile, run_rc):
    log = sim_log(tile)
    res = replay_result(open(log, errors="replace").read()) if log else \
        {"finished": False, "checked_from": None, "app_start": None, "pre_app_x": 0, "pre_app_x_examples": [],
         "mismatches": None, "x_mismatches": None, "first_cycle": None, "last_cycle": None, "ports": {},
         "examples": [], "lines": []}
    res.update(tile=tile, sim_log=log, run_rc=run_rc,
               report=os.path.isfile(f"outputs/reports/{tile}.hier"))
    res["problems"] = problems_of(res)
    lines = res.pop("lines")
    if lines:
        with open(f"outputs/reports/{tile}.mismatches.txt", "w") as f:
            f.write("\n".join(lines) + "\n")
    with open(f"outputs/reports/{tile}.replay.json", "w") as f:
        json.dump(res, f, indent=1)
    return res


def main():
    design = os.environ.get("design_name")
    mode = os.environ.get("replay_check") or "auto"
    if mode == "auto":
        mode = "fail" if os.environ.get("app_bundle") else "warn"
    os.makedirs("outputs/reports", exist_ok=True)
    results = []
    for tile in tile_ids(design):
        os.environ["tile_id"] = tile
        rc = subprocess.run(["./run.sh"]).returncode
        results.append(check_tile(tile, rc))

    lines = [f"{r['tile']}: {'; '.join(r['problems']) or 'OK'}"
             + (f" ({r['pre_app_x']} X outputs before the app start at cycle {r['app_start']} not counted)"
                if r["pre_app_x"] else "") for r in results]
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
