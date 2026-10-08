"""Genus name map -> PrimeTime RTL-to-gate name mapping for read_saif.

  python namemap_to_pt.py inputs/design.namemap namemap.pt.tcl

Genus `write_name_mapping` (what cadence-genus-synthesis outputs as
design.namemap) writes Conformal LEC commands, one per mapped point:
    add mapped point <rtl>/q <gate inst>/Q  -type DFF DFF
PrimeTime cannot `source` that. For each register this writes
    set_rtl_to_gate_name -rtl <rtl net> -gate <net on the gate's Q pin>
(QN duplicates and ports, which keep their names, are skipped) so an RTL-sim
SAIF annotates the registers; PT propagates the rest. A file that is already
PrimeTime Tcl (no `add mapped point` lines) is copied unchanged.
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
lines = open(src).read().splitlines()
points = [re.match(r"\s*add mapped point (\S+) (\S+)\s+-type (\S+)", l) for l in lines]
points = [m for m in points if m]
with open(dst, "w") as f:
    if not points:
        f.write("\n".join(lines) + "\n")
        sys.exit(0)
    seen = set()
    for m in points:
        rtl, gate, kind = m.groups()
        if kind in ("PI", "PO") or not re.search(r"/Q$", gate):
            continue
        net = re.sub(r"/q$", "", rtl)
        if net in seen:
            continue
        seen.add(net)
        f.write(f"catch {{set_rtl_to_gate_name -rtl {{{net}}} "
                f"-gate [get_object_name [get_nets -of_objects [get_pins {{{gate}}}]]]}}\n")
print(f"{src}: {len(points)} mapped points -> {len(seen)} register mappings in {dst}")
