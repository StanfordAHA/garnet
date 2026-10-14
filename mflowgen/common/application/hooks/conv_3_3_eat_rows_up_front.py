#!/usr/bin/env python3
"""Pre-PnR hook (gen_app_bundle.py --pre-pnr-hook): rewrite a dense-RV 3x3
line-buffer design (conv_3_3) so the newest row is "eaten up front" through the
MEM's filter path (version B of the conv_3_3 A/B study, mflowgen/CLAUDE.md).

Today (version A) the newest-row tap is a wire from the input IO, both SRAM
readers stream the whole W x H frame offset by 1 and 2 rows (address
precursors), the PE fires on every input token and the GLB store keeps the
valid window (start 2W+2). This hook makes version B:
  * input IO -> MEM filter-in (data_in_<in_ports>), whose item filter drops rows
    0-1; filter-out (data_out_<out_ports>) replaces the IO as the newest tap;
  * SRAM readers walk W x (H-2): the row r-2 tap reads rows 0..H-3, the row
    r-1 tap rows 1..H-2;
  * dependences as lake "lake_constraints" (the dep_values encodings cannot
    say "this reader's data row leads its iteration row"); none on the filter
    pair when the spec's filter path is a FIFO (build_spec_rv
    filter_fifo_depth), else FIFO-like ones on the general filter buffer;
  * the GLB store starts at 2 (only the first two columns of a row dropped).
The MEM instance gets a third in/out port pair, so map and PnR need
METAMAPPER_MEM_PORTS=3 (MetaMapper's cgralib.Mem has 2 by default).
usage: conv_3_3_eat_rows_up_front.py <app>/bin
       (env LAKE_SPEC_CONFIG: in_ports, out_ports, filter_fifo_depth)"""
import json
import os
import sys

bin_dir = sys.argv[1]
path = os.path.join(bin_dir, "design_top.json")
orig = os.path.join(bin_dir, "design_top.pre_fp_hook.json")
if not os.path.exists(orig):          # idempotent: always start from the mapped design
    os.replace(path, orig)
d = json.load(open(orig))
spec = json.load(open(os.environ["LAKE_SPEC_CONFIG"])) if os.environ.get("LAKE_SPEC_CONFIG") else {}
n_in, n_out = spec.get("in_ports", 2), spec.get("out_ports", 2)

mods = d["namespaces"]["global"]["modules"]
top = d["top"].split(".", 1)[1]          # e.g. "global.conv_3_3"
mod = mods[top]
insts, conns = mod["instances"], mod["connections"]
mems = [n for n, i in insts.items() if str(i.get("genref", "")).startswith("cgralib.Mem")
        and "dep_values" in (i.get("metadata", {}).get("config") or {})]
assert len(mems) == 1, f"expected one RV line-buffer MEM, got {mems}"
mem = mems[0]
cfg = insts[mem]["metadata"]["config"]
pm = cfg["port_mappings"]
port_of = {op: v.split(".")[-1] for op, v in pm.items()}
writers = [op for op, p in port_of.items() if p.startswith("data_in_")]
readers = [op for op, p in port_of.items() if p.startswith("data_out_")]
assert len(writers) == 1 and len(readers) == 2, port_of
wop = writers[0]
assert port_of[wop] == "data_in_0"
W, H = cfg["domain"][wop]["extents"]
assert cfg["access_map"][wop]["address_stride"] == [1, W] and cfg["access_map"][wop]["address_offset"] == [0]
lag = {}
for op in readers:
    rows = [v for lvl, v in cfg["precursor_deltas"][op] if lvl == 1]
    assert cfg["domain"][op]["extents"] == [W, H], (op, cfg["domain"][op])
    lag[op] = rows[0]
by_lag = {v: op for op, v in lag.items()}
assert set(by_lag) == {1, 2}, lag
r1_port, r2_port = port_of[by_lag[1]], port_of[by_lag[2]]
lk = lambda p: ("port_w" + p[len("data_in_"):]) if p.startswith("data_in_") else ("port_r" + p[len("data_out_"):])

# the MEM instance gets the filter-path ports
ga = insts[mem]["genargs"]
assert ga["num_inputs"][1] == n_in and ga["num_outputs"][1] == n_out, ga
ga["num_inputs"][1], ga["num_outputs"][1] = n_in + 1, n_out + 1

# --- rewire the newest tap ------------------------------------------------
mem_in0 = f"{mem}.data_in_0"
src = [b if a == mem_in0 else a for a, b in conns if mem_in0 in (a, b)]
assert len(src) == 1, src
src = src[0]
fi, fo = f"{mem}.data_in_{n_in}", f"{mem}.data_out_{n_out}"
moved = 0
for c in conns:
    if src in c and mem_in0 not in c:
        c[c.index(src)] = fo
        moved += 1
assert moved >= 1
conns.append([src, fi])

# --- MEM program (version B) ------------------------------------------------
rows = H - 2
two_d = lambda off: {"address_offset": [off], "address_stride": [1, W], "dimensionality": [2]}
dom = lambda h: {"dimensionality": [2], "extents": [W, h]}
FI, FO, R1, R2 = "fp_newest_in", "fp_newest_out", by_lag[1], by_lag[2]
new = dict(cfg)
new["port_mappings"] = {wop: pm[wop], R2: pm[R2], R1: pm[R1],
                        FI: f"{mem.split('$')[-1]}.data_in_{n_in}", FO: f"{mem.split('$')[-1]}.data_out_{n_out}"}
new["dep_values"] = {}
new["precursor_deltas"] = {}
new["domain"] = {wop: dom(H), R2: dom(rows), R1: dom(rows), FI: dom(rows), FO: dom(rows)}
new["access_map"] = {wop: two_d(0), R2: two_d(0), R1: two_d(W), FI: two_d(0), FO: two_d(0)}
new["filter"] = {FI: {"offset": [2 * W], "stride": [1, W]}}
pw, pr1, pr2, pfi, pfo = "port_w0", lk(r1_port), lk(r2_port), f"port_w{n_in}", f"port_r{n_out}"
new["lake_constraints"] = [
    # row r-2 tap reads row k at iteration k: row k written. Row level: the
    # column-level zero-lag form [pr2, 0, pw, 0, "LT", 2*fw*vc + 4] has a
    # one-row wrap fixup and deadlocks once the writer runs 3 rows ahead in an
    # early column (newest-tap path shallower than ~2*fw*vc + 4 words).
    [pr2, 1, pw, 1, "LT", 0],
    [pr1, 1, pw, 1, "LT", 1],                   # row r-1 tap reads row k+1 at iteration k
    [pw, 1, pr2, 1, "GT", 8],                   # writer within 8 rows of each SRAM reader
    [pw, 1, pr1, 1, "GT", 8],
]
if spec.get("filter_fifo_depth") is None:
    # general filter buffer (8 words per fetch-width word): run it as a FIFO.
    # A FIFO filter path (build_spec_rv filter_fifo_depth) is one in hardware.
    new["lake_constraints"] += [
        [pfo, 0, pfi, 0, "LT", 6],
        [pfi, 0, pfo, 0, "GT", 28],
    ]
for k in ("domain_diff", "new_domain", "original_domain"):
    new.pop(k, None)
insts[mem]["metadata"]["config"] = new

# --- GLB store schedule: drop only the first two columns of each row ---------
outs = [n for n, i in insts.items() if "in2glb_0" in i.get("metadata", {})]
assert len(outs) == 1, outs
sched = insts[outs[0]]["metadata"]["in2glb_0"]
assert sched["cycle_starting_addr"] == [2 * W + 2] and sched["cycle_stride"] == [1, W], sched
sched["cycle_starting_addr"] = [2]

json.dump(d, open(path, "w"), indent=1)
print(f"fp_hook: {mem}: newest tap {src} -> {fi} / {fo} ({moved} consumers); "
      f"R2={R2}({r2_port}) R1={R1}({r1_port}); store start {2 * W + 2} -> 2")
