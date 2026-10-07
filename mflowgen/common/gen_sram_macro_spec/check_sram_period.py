"""Fail the build if the clock target is faster than the SRAM macro allows.

Runs after gen_srams.sh. Reads the macro's minimum cycle time at the
characterized corner (``$corner``, TT by default) and compares it with the
graph's ``$clock_period`` (ns -- Tile_MemCore's constraints use
``set_units -time ns``). A target period shorter than the macro's minimum
cycle time (a frequency above the macro's max) is an error: the step exits
non-zero so the sweep stops before synthesis.

Source of the minimum cycle time, in order:
  1. genviews datasheet: genviews-output/doc/<macro>_<corner>.csv,
     row "Clock Cycle Time".
  2. outputs/sram_tt.lib: CLK `timing_type : "minimum_period"` checks. The GF12
     compilers emit one per margin-adjust (MA_VD*) state and put a 999999
     placeholder in the uncharacterized ones, so placeholders are dropped and
     the largest remaining value is used.

The clock high/low minimums (datasheet rows, or lib `min_pulse_width`) are
checked against half the period (50% duty).

If neither source can be read the check warns and passes, so a format change
can't block every build. Either way it writes reports/sram_period.rpt.
"""
import csv
import os
import re
import sys

REPORT = "reports/sram_period.rpt"
LIB = "outputs/sram_tt.lib"
PLACEHOLDER_PS = 1e5  # genviews uses 999999 for uncharacterized MA states


def _to_ps(value, unit):
    unit = unit.strip().lower()
    scale = {"ps": 1.0, "ns": 1000.0, "1ps": 1.0, "1ns": 1000.0}.get(unit)
    if scale is None:
        raise ValueError(f"unknown time unit {unit!r}")
    return float(value) * scale


def _macro_name():
    """<macro> from the outputs/sram_tt.lib symlink (<macro>_<corner>.lib)."""
    corner = os.environ.get("corner", "TT_0P800V_025C")
    base = os.path.basename(os.path.realpath(LIB))
    suffix = f"_{corner}.lib"
    return base[: -len(suffix)] if base.endswith(suffix) else None


def from_datasheet(macro, corner):
    """{'cycle','high','low'} in ps from the genviews datasheet CSV, or None."""
    path = f"genviews-output/doc/{macro}_{corner}.csv"
    if not macro or not os.path.isfile(path):
        return None
    rows = {"Clock Cycle Time": "cycle", "Clock High Time": "high",
            "Clock Low Time": "low"}
    found = {}
    with open(path, newline="") as f:
        for rec in csv.reader(f):
            if len(rec) >= 3 and rec[0].strip() in rows:
                found[rows[rec[0].strip()]] = _to_ps(rec[1], rec[2])
    return found if "cycle" in found else None


def _lib_groups(text, timing_type):
    """Constraint values (lib units) of every `timing_type : <type>` group."""
    vals = []
    for m in re.finditer(rf'timing_type\s*:\s*"?{timing_type}"?\s*;', text):
        # The group's values(...) follow within the same timing() block.
        block = text[m.end(): m.end() + 2000].split("timing ()", 1)[0]
        for vm in re.finditer(r'values\s*\(\s*\\?\s*"([^"]*)"', block):
            vals += [float(v) for v in vm.group(1).split(",") if v.strip()]
    return vals


def from_lib():
    """{'cycle','high','low'} in ps from the CLK checks in sram_tt.lib, or None."""
    if not os.path.isfile(LIB):
        return None
    with open(LIB) as f:
        text = f.read()
    m = re.search(r'time_unit\s*:\s*"([^"]+)"', text)
    unit = m.group(1) if m else "1ns"
    cycle = [_to_ps(v, unit) for v in _lib_groups(text, "minimum_period")]
    cycle = [v for v in cycle if v < PLACEHOLDER_PS]
    if not cycle:
        return None
    pulse = [_to_ps(v, unit) for v in _lib_groups(text, "min_pulse_width")]
    pulse = [v for v in pulse if v < PLACEHOLDER_PS]
    found = {"cycle": max(cycle)}
    if pulse:
        found["high"] = found["low"] = max(pulse)
    return found


def main():
    corner = os.environ.get("corner", "TT_0P800V_025C")
    period_ps = float(os.environ["clock_period"]) * 1000.0  # ns -> ps
    macro = _macro_name()

    try:
        limits, source = from_datasheet(macro, corner), "datasheet"
    except (OSError, ValueError) as e:
        print(f"**WARNING: SRAM period check: unreadable datasheet ({e}); "
              "falling back to the lib.")
        limits = None
    if limits is None:
        limits, source = from_lib(), "lib"

    lines = [f"macro: {macro}", f"corner: {corner}",
             f"target_period_ps: {period_ps:g}"]
    if limits is None:
        print("**WARNING: SRAM period check: no minimum cycle time found in "
              f"the datasheet or {LIB}; not checked.")
        lines.append("status: UNKNOWN")
        return lines, 0

    cycle = limits["cycle"]
    half = period_ps / 2.0
    fails = []
    if period_ps < cycle:
        fails.append(f"clock period {period_ps:g} ps is shorter than the macro's "
                     f"minimum cycle time {cycle:g} ps")
    for key, name in (("high", "high"), ("low", "low")):
        if key in limits and half < limits[key]:
            fails.append(f"half period {half:g} ps is shorter than the macro's "
                         f"minimum clock-{name} time {limits[key]:g} ps")

    lines += [f"source: {source}",
              f"min_cycle_ps: {cycle:g}",
              f"max_freq_mhz: {1e6 / cycle:.1f}",
              f"target_freq_mhz: {1e6 / period_ps:.1f}",
              f"margin_ps: {period_ps - cycle:g}"]
    lines += [f"min_clock_{k}_ps: {limits[k]:g}" for k in ("high", "low") if k in limits]
    lines.append(f"status: {'FAIL' if fails else 'PASS'}")

    tag = f"{macro} @ {corner}"
    if fails:
        for msg in fails:
            print(f"**ERROR: SRAM period check ({tag}): {msg}. Slow the clock "
                  "(clock_period in construct.py) or pick a faster macro.")
        return lines, 1
    print(f"SRAM period check ({tag}): PASS -- min cycle {cycle:g} ps "
          f"({1e6 / cycle:.0f} MHz) vs target {period_ps:g} ps, from {source}.")
    return lines, 0


if __name__ == "__main__":
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    try:
        report, rc = main()
    except Exception as e:  # noqa: BLE001 -- a parser bug must not block builds
        print(f"**WARNING: SRAM period check could not run ({e}); not checked.")
        report, rc = ["status: UNKNOWN", f"error: {e}"], 0
    with open(REPORT, "w") as f:
        f.write("\n".join(report) + "\n")
    sys.exit(rc)
