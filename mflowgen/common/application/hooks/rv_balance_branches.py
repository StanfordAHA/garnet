#!/usr/bin/env python3
"""Pre-PnR hook (gen_app_bundle.py --pre-pnr-hook): give a dense ready-valid design
full throughput by balancing its reconvergent branches with pure buffering.

In RV every register is a 2-deep FIFO and a fanout is a lazy fork: a token leaves
only when every branch takes it. When the branches of a fork rejoin at a PE with
different latencies (a row tap feeding a multiply-add chain directly and through
the stencil's delay registers), the short branch must hold every token the long
branch has in flight. Without enough FIFO stages on it the loop caps the rate
(conv_3_3: 3/4 and 2/3 tokens/cycle). RV maps with MATCH_BRANCH_DELAY=0 (an
inserted static register would be a data delay), so nothing balances them.

Pads netlist edges with plain coreir.reg instances, metadata extra_data 0: canal
configures those as FIFOs with no initial token, so data is unchanged (only
latency and buffering are added). Two ways to choose the edges:
- --plan JSON {"<instance>.<input port>": registers} (env RV_BALANCE_PLAN): exactly
  those, computed on the routed design by gen_app_bundle.py --rv-balance
  (rv_throughput.py), which sets --pe-stages 0. This is what reaches full rate.
- --pe-stages N > 0: pre-PnR estimate. The arrival of each PE input in FIFO stages
  from every data source (input IO, MEM output; PE = N, register = 1 + its pre-filled
  tokens), and every earlier input of a PE padded up to its latest one. It ignores
  the registers routing adds (one per hop), so alone it does not reach full rate.
Constant inputs are ignored. MEM inputs are not balanced (a MEM decouples them).

usage: rv_balance_branches.py <app>/bin [--plan JSON] [--pe-stages N] [--margin N]
Idempotent: the first run keeps design_top.pre_rv_balance.json and later runs start
from it, unless an earlier hook rewrote design_top.json since (then that is used).
"""
import argparse
import hashlib
import json
import os

MARK = "rv_balance"


def endpoints(inst, conns):
    """Directed data edges [(src "inst.port", dst "inst.port")] of the top module."""
    def kind(ep):
        name, port = ep.split(".", 1)
        if name == "self":
            return None
        i = inst.get(name, {})
        ref = str(i.get("genref", i.get("modref", "")))
        if ref in ("coreir.const", "corebit.const"):
            return "src"
        if ref == "global.PE":
            return "src" if port.startswith("O") else "dst"
        if ref.startswith("cgralib.Mem") or ref.startswith("cgralib.Pond"):
            return "src" if "out" in port else "dst"
        if ref in ("coreir.reg", "corebit.reg"):
            return "src" if port == "out" else "dst"
        if ref == "global.IO" or ref == "global.BitIO":
            return "src" if port == "out" else "dst"
        return None
    edges = []
    for a, b in conns:
        ka, kb = kind(a), kind(b)
        if ka == "src" and kb == "dst":
            edges.append((a, b))
        elif kb == "src" and ka == "dst":
            edges.append((b, a))
    return edges


def balance(d, pe_stages, margin, plan=None):
    top = d["top"].split(".", 1)[1]
    mod = d["namespaces"]["global"]["modules"][top]
    inst, conns = mod["instances"], mod["connections"]
    if (mod.get("metadata") or {}).get(MARK):
        raise SystemExit("design already balanced")
    edges = endpoints(inst, conns)
    ref = lambda n: str(inst[n].get("genref", inst[n].get("modref", "")))
    ins = {}
    for s, t in edges:
        ins.setdefault(t.split(".")[0], []).append((s, t))
    arrival = {}   # instance -> arrival (stages) at its output; None = constant

    def arr(n, stack=()):
        if n in arrival:
            return arrival[n]
        r = ref(n)
        if r in ("coreir.const", "corebit.const"):
            a = None
        elif r.startswith("cgralib.Mem") or r.startswith("cgralib.Pond") or r == "global.IO" or r == "global.BitIO":
            a = 0   # a memory decouples its inputs from its outputs
        else:
            if n in stack:
                raise SystemExit(f"combinational loop through {n}")
            srcs = [arr(s.split(".")[0], stack + (n,)) for s, _ in ins.get(n, [])]
            srcs = [x for x in srcs if x is not None]
            if not srcs:
                a = None   # only constants: a constant PE
            elif r in ("coreir.reg", "corebit.reg"):
                a = max(srcs) + 1 + int((inst[n].get("metadata") or {}).get("extra_data", 0))
            else:
                a = max(srcs) + pe_stages
        arrival[n] = a
        return a

    added, report = 0, []
    for n in sorted(ins):
        if ref(n) != "global.PE" or pe_stages <= 0:
            continue
        arr(n)
        inputs = [(s, t, arr(s.split(".")[0])) for s, t in ins[n]]
        known = [a for _, _, a in inputs if a is not None]
        if len(known) < 2:
            continue
        top_a = max(known)
        for s, t, a in inputs:
            if a is None or a >= top_a:
                continue
            k = top_a - a + margin
            added = insert_regs(inst, conns, s, t, k, added)
            report.append((t, top_a - a, k))
    for t, k in sorted((plan or {}).items()):
        srcs = [s for s, tt in edges if tt == t]
        if len(srcs) != 1:
            raise SystemExit(f"plan: {t} has {len(srcs)} drivers")
        added = insert_regs(inst, conns, srcs[0], t, k, added)
        report.append((t, None, k))
    mod.setdefault("metadata", {})[MARK] = {"pe_stages": pe_stages, "margin": margin, "plan": plan,
                                            "registers": added}
    return added, report


def insert_regs(inst, conns, s, t, k, added):
    """Put k pass-through registers (extra_data 0) on the connection s -> t, named
    after the input they pad (rv_balance_<hash of t>_<i>, i = 0 nearest the driver),
    so a register keeps its name when a later plan adds more on the same input."""
    width = 16
    sw = inst[s.split(".")[0]].get("genargs", {}).get("width")
    if isinstance(sw, list):
        width = sw[1]
    tag = hashlib.md5(t.encode()).hexdigest()[:8]
    prev = s
    for i in range(k):
        rn = f"rv_balance_{tag}_{i}"
        added += 1
        inst[rn] = {"genref": "coreir.reg", "genargs": {"width": ["Int", width]},
                    "modargs": {"clk_posedge": ["Bool", True],
                                "init": [["BitVector", width], f"{width}'h0"]},
                    "metadata": {"extra_data": 0}}
        conns.append([prev, f"{rn}.in"])
        prev = f"{rn}.out"
    for c in conns:
        if sorted(c) == sorted([s, t]):
            c[c.index(s)] = prev
            return added
    raise SystemExit(f"no connection {s} -> {t}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("bin_dir")
    p.add_argument("--pe-stages", type=int, default=int(os.environ.get("RV_BALANCE_PE_STAGES", 3)),
                   help="FIFO stages counted per PE (input FIFO, ALU, output FIFO); default 3 "
                        "(env RV_BALANCE_PE_STAGES)")
    p.add_argument("--margin", type=int, default=int(os.environ.get("RV_BALANCE_MARGIN", 0)),
                   help="extra registers on every padded (early) input")
    p.add_argument("--plan", default=os.environ.get("RV_BALANCE_PLAN"),
                   help='JSON {"<instance>.<input port>": registers}: pad exactly those inputs '
                        "(from a routed design's throughput model); with --pe-stages 0 only "
                        "these (env RV_BALANCE_PLAN)")
    a = p.parse_args()
    path = os.path.join(a.bin_dir, "design_top.json")
    orig = os.path.join(a.bin_dir, "design_top.pre_rv_balance.json")
    d = json.load(open(path))
    top = d["top"].split(".", 1)[1]
    if (d["namespaces"]["global"]["modules"][top].get("metadata") or {}).get(MARK):
        d = json.load(open(orig))     # our own output: start again from the saved input
    else:
        json.dump(d, open(orig, "w"))
    plan = json.load(open(a.plan)) if a.plan else None
    added, report = balance(d, a.pe_stages, a.margin, plan)
    json.dump(d, open(path, "w"), indent=1)
    for t, diff, k in report:
        why = "planned" if diff is None else f"{diff} stages early"
        print(f"rv_balance: {t}: {why} -> {k} registers")
    print(f"rv_balance: {added} registers (pe_stages {a.pe_stages}, margin {a.margin})")


if __name__ == "__main__":
    main()
