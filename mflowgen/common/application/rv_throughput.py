"""Throughput model of a routed dense ready-valid design, and the latency matching that
brings it to full rate (gen_app_bundle.py --rv-balance; mflowgen/CLAUDE.md "RV branch
balancing").

Storage: every routing REG node is a FIFO of depth `reg_depth` (canal RegFIFO, ready =
~full); netlist registers start with `extra_data` tokens (stencil delays). A PE has
one input FIFO per used input and an output FIFO (depth pe_in / pe_out), plus a
2-deep primitive output FIFO when enabled (prim_out); its FIFOs start with the PE's
pre-fill (design_top metadata ".dataN": num_input_fifo on input N, num_output_fifo on
the output: clockwork's column-offset stencil taps), so a pre-filled input must arrive
that many stages later than the others (camera_pipeline_2x2 2026-10-28: balanced
without it, every pre-filled join stayed one stage early and capped the app at 3/4
rate, 16,459 vs 12,562 ns static); it fires when every input FIFO
holds a token and its output FIFO is not full. Fanouts are lazy forks: a token
leaves only when every branch's next FIFO is ready (start-of-cycle counts). MEM and
pond outputs, the input IO and constant PEs are always-valid sources; MEM and pond
inputs and the output IO are always-ready sinks (so a pond accumulation loop is not
modelled). A PE with both outputs used (res, res_p) fires into both. Reports the output
IO's rate. An in-tile core-to-core wire (a pond packed into its PE: the route goes
PondTop_output -> PE_input with no switch box) holds no padding register: its consumer
is in Model.fixed, and the plans leave such an input early instead of padding it.
Neither do they pad a PE input on a loop through a memory (Model.loop_in: an
accumulation, a MEM or pond output feeding back into that memory's input): the model
does not see such loops, and a register on one is paid on every iteration (resnet_pond
2026-10-28: 220,031 ns balanced vs 177,697 with this rule).

Validated against xrun of conv_3_3 PnR results (A/B, 2026-10-13/14): modelled rates
0.750 / 0.667 / 0.722 / 0.765 unbalanced and 1.000 balanced = measured.

usage: rv_throughput.py <app bin dir>  (modelled rate + the next balancing step)"""
import json
import re
import sys
from collections import defaultdict
from itertools import combinations


def strongly_connected(graph):
    """{node: component root} of a directed graph {node: successors} (iterative Tarjan)."""
    index, low, on_stack, stack, comp, count = {}, {}, set(), [], {}, 0
    for root in list(graph):
        if root in index:
            continue
        index[root] = low[root] = count
        count += 1
        stack.append(root)
        on_stack.add(root)
        work = [(root, iter(graph.get(root, ())))]
        while work:
            v, it = work[-1]
            w = next(it, None)
            if w is not None:
                if w not in index:
                    index[w] = low[w] = count
                    count += 1
                    stack.append(w)
                    on_stack.add(w)
                    work.append((w, iter(graph.get(w, ()))))
                elif w in on_stack:
                    low[v] = min(low[v], index[w])
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                while True:
                    x = stack.pop()
                    on_stack.discard(x)
                    comp[x] = v
                    if x == v:
                        break
    return comp


def parse_route(path):
    nets, cur = {}, None
    for line in open(path):
        m = re.match(r"Net ID: (\S+)", line)
        if m:
            cur = m.group(1)
            nets[cur] = []
            continue
        if line.startswith("Segment:"):
            nets[cur].append([])
            continue
        m = re.match(r"\s*(PORT|REG|SB|RMUX)\s*(\S*)\s*\(([\d,\s]+)\)", line)
        if m:
            nets[cur][-1].append((m.group(1), m.group(2), tuple(int(x) for x in m.group(3).split(","))))
    return nets


class Model:
    def __init__(self, route, place, design_top, reg_depth=2, pe_in=2, pe_out=2, rom_depth=2):
        self.nets = parse_route(route)
        # netlist registers placed at (x, y) on track name -> instance name
        self.netreg = {}
        self.pe_kind = {}
        pe_at, mem_at = {}, {}
        for line in open(place).read().splitlines()[2:]:
            w = line.split()
            if len(w) < 4:
                continue
            name, x, y, bid = w[0], int(w[-3]), int(w[-2]), w[-1]
            if bid.startswith("#r") and "@" in name:
                inst, track = name.split("@")
                self.netreg[(x, y, track)] = inst
            if bid.startswith("#p"):
                self.pe_kind[(x, y)] = name
                pe_at[name] = (x, y)
            if bid.startswith("#m"):
                mem_at[name] = (x, y)
        d = json.load(open(design_top))
        top = d["top"].split(".", 1)[1]
        insts = d["namespaces"]["global"]["modules"][top]["instances"]
        self.extra = {n: int((i.get("metadata") or {}).get("extra_data", 0)) for n, i in insts.items()}
        # PE FIFO pre-fill (garnet core_combiner_core: ".dataN" -> input N, num_output_fifo
        # -> the output): (x, y) -> ({input index: tokens}, output tokens)
        self.pe_fill = {}
        for n, i in insts.items():
            fill = {k[len(".data"):]: v for k, v in (i.get("metadata") or {}).items()
                    if k.startswith(".data") and isinstance(v, dict)}
            if fill and n in pe_at:
                self.pe_fill[pe_at[n]] = ({int(k): int(v.get("num_input_fifo", 0)) for k, v in fill.items()},
                                          max(int(v.get("num_output_fifo", 0)) for v in fill.values()))
        # ROM tiles (design_top metadata is_rom): (x, y)
        self.rom_tiles = {mem_at[n] for n, i in insts.items()
                          if n in mem_at and (i.get("metadata") or {}).get("is_rom")}
        self.reg_depth, self.pe_in, self.pe_out, self.rom_depth = reg_depth, pe_in, pe_out, rom_depth
        self.prim_out = set()   # PEs (x, y) whose primitive output FIFO is enabled (+1 stage)
        self.build()

    def node_id(self, node):
        kind, name, c = node
        if kind == "REG":
            track, x, y, w = c
            return ("REG", name, x, y, w)
        if kind == "PORT":
            return ("PORT", name, c[0], c[1])
        return (kind, name, c)

    def build(self):
        succ = defaultdict(set)
        rmux_in = defaultdict(set)
        # consumers reached over an in-tile core-to-core wire (PORT -> PORT, no switch box):
        # no padding register can go on that edge
        self.fixed = set()
        for net, segs in self.nets.items():
            for seg in segs:
                ids = [self.node_id(n) for n in seg]
                for a, b in zip(ids, ids[1:]):
                    succ[a].add(b)
                    if a[0] == "PORT" and b[0] == "PORT":
                        self.fixed.add(b)
                    if b[0] == "RMUX":
                        rmux_in[(net, b)].add(a[0])
        # an RMUX reached through its register in one segment and around it in another
        # has no single configuration (archipelago before de8e844): not modelled
        problems = sorted(f"{net} {b}" for (net, b), kinds in rmux_in.items() if len(kinds) > 1)
        if problems:
            raise ValueError("inconsistent route (RMUX reached through and around its register): "
                             + "; ".join(problems))
        # storage elements: REG nodes, PE input FIFOs (PORT PE_input), PE output FIFOs (PORT PE_output)
        self.cap, self.init = {}, {}
        nodes = set(succ) | {b for v in succ.values() for b in v}
        for n in nodes:
            if n[0] == "REG":
                inst = self.netreg.get((n[2], n[3], n[1]))
                self.cap[n] = self.reg_depth
                self.init[n] = self.extra.get(inst, 0) if inst else 0
            elif n[0] == "PORT" and n[1].startswith("PE_input"):
                self.cap[n] = self.pe_in
                fill = self.pe_fill.get((n[2], n[3]), ({}, 0))[0]
                width, index = re.match(r"PE_input_width_(\d+)_num_(\d+)$", n[1]).groups()
                self.init[n] = fill.get(int(index), 0) if width != "1" else 0
            elif n[0] == "PORT" and n[1].startswith("PE_output"):
                self.cap[n] = self.pe_out
                self.init[n] = self.pe_fill.get((n[2], n[3]), ({}, 0))[1] if "_width_1_" not in n[1] else 0
        # A ROM is a pipeline, not a source and a sink: tile input FIFO -> StrgRAMRV SRAM
        # read -> data FIFO, one read per cycle. Its MEM ports are storage with a
        # ("ROM", x, y) stage between them (2-deep each: the model's FIFOs pass a token
        # per cycle only from depth 2). It times nothing a join sees (a ROM output feeds
        # an output IO), but without it the output IO rate of an app whose outputs come
        # from ROMs is always full (camera_pipeline_2x2).
        rom_ports = defaultdict(lambda: ([], []))
        for n in nodes:
            if self.is_rom_port(n):
                rom_ports[(n[2], n[3])]["_output" in n[1]].append(n)
                self.cap[n], self.init[n] = self.rom_depth, 0
        for xy in rom_ports:
            self.cap[("ROM",) + xy], self.init[("ROM",) + xy] = self.rom_depth, 0
        # consumers of each producer: storage/sink nodes reachable through wires (SB/RMUX)
        self.fanout = {}
        for n in nodes:
            if n in self.cap or self.is_source(n):
                outs, stack, seen = [], list(succ.get(n, ())), set()
                while stack:
                    m = stack.pop()
                    if m in seen:
                        continue
                    seen.add(m)
                    if m in self.cap or m[0] == "PORT":
                        outs.append(m)
                    else:
                        stack.extend(succ.get(m, ()))
                self.fanout[n] = outs
        for xy, (ins, outs) in rom_ports.items():
            for i in ins:
                self.fanout[i] = [("ROM",) + xy]
            self.fanout[("ROM",) + xy] = list(outs)
        # PEs: (x, y) -> input ports, output port
        self.pes = defaultdict(lambda: {"in": [], "out": []})
        for n in nodes:
            if n[0] == "PORT" and n[1].startswith("PE_input"):
                self.pes[(n[2], n[3])]["in"].append(n)
            elif n[0] == "PORT" and n[1].startswith("PE_output"):
                self.pes[(n[2], n[3])]["out"].append(n)
        self.loop_in = self.memory_loop_inputs(nodes)

    def memory_loop_inputs(self, nodes):
        """PE inputs on a loop through a memory: the dataflow graph plus an edge from
        each MEM / pond input port to that core's output ports (same tile, same core),
        then every PE input whose producer is in its strongly connected component."""
        graph = defaultdict(set)
        for p, cons in self.fanout.items():
            graph[p].update(cons)
        for pe in self.pes.values():
            for i in pe["in"]:
                graph[i].update(pe["out"])
        ports = defaultdict(lambda: ([], []))
        for n in nodes:
            if n[0] == "PORT" and not n[1].startswith(("PE_", "io2f", "f2io")):
                ports[(n[2], n[3], n[1].split("_")[0])]["_output" in n[1]].append(n)
        for ins, outs in ports.values():
            for i in ins:
                graph[i].update(outs)
        comp = strongly_connected(graph)
        return {c for p, cons in self.fanout.items() for c in cons
                if c[0] == "PORT" and c[1].startswith("PE_input") and comp.get(p) == comp.get(c)}

    def unpaddable(self, n):
        """No padding register may go in front of PE input n (Model.fixed, Model.loop_in)."""
        return n in self.fixed or n in self.loop_in

    def is_source(self, n):
        # MEM / pond outputs (MEM_output_*, PondTop_output_*) and the input IOs; not a ROM
        return n[0] == "PORT" and (n[1].startswith("io2f")
                                   or ("_output" in n[1] and not n[1].startswith("PE_output")
                                       and not self.is_rom_port(n)))

    def is_sink(self, n):
        return n[0] == "PORT" and (n[1].startswith("f2io")
                                   or ("_input" in n[1] and not n[1].startswith("PE_input")
                                       and not self.is_rom_port(n)))

    def is_rom_port(self, n):
        return n[0] == "PORT" and n[1].startswith("MEM_") and (n[2], n[3]) in self.rom_tiles

    def const_pe(self, xy):
        return "const" in self.pe_kind.get(xy, "") or not self.pes[xy]["in"]

    def const_out(self, n):
        return n[0] == "PORT" and n[1].startswith("PE_output") and self.const_pe((n[2], n[3]))

    def run(self, cycles=6000, warm=1000):
        """Simulate; -> (tokens per cycle at the output IO after `warm` cycles, final counts)."""
        cap = dict(self.cap)
        cnt = dict(self.init)
        for xy in self.prim_out:
            cap[("PRIM", xy)] = 2
            cnt[("PRIM", xy)] = 0
        out = 0
        out_hist = []
        for cyc in range(cycles):
            ready = {n: cnt[n] < cap[n] for n in cnt}
            pops, pushes = defaultdict(int), defaultdict(int)
            # producers: sources, REG FIFOs, PE output FIFOs
            for p, cons in self.fanout.items():
                if p[0] == "PORT" and p[1].startswith("PE_input"):
                    continue   # PE inputs feed the PE core, not a route
                const = self.const_out(p)
                if not (self.is_source(p) or const or cnt.get(p, 0) > 0) or not cons:
                    continue
                if all(self.is_sink(c) or ready.get(c, False) for c in cons):
                    if p in cnt and not const:
                        pops[p] += 1
                    for c in cons:
                        if not self.is_sink(c):
                            pushes[c] += 1
                        elif c[1].startswith("f2io"):
                            out += 1
            # PE cores (through the primitive output FIFO when it is enabled); a PE with
            # both outputs used fires when both output FIFOs have room
            for xy, pe in self.pes.items():
                if self.const_pe(xy) or not pe["out"]:
                    continue
                if xy in self.prim_out:
                    o, stage = pe["out"][0], ("PRIM", xy)
                    if cnt[stage] > 0 and ready[o]:
                        pops[stage] += 1
                        pushes[o] += 1
                    stages = [stage] + pe["out"][1:]
                else:
                    stages = pe["out"]
                if all(cnt[i] > 0 for i in pe["in"]) and all(ready[st] for st in stages):
                    for i in pe["in"]:
                        pops[i] += 1
                    for st in stages:
                        pushes[st] += 1
            for n, k in pops.items():
                cnt[n] -= k
            for n, k in pushes.items():
                cnt[n] += k
            out_hist.append(out)
        rate = (out_hist[-1] - out_hist[warm]) / (cycles - 1 - warm)
        return rate, cnt


def netlist_sink(m, node):
    """The netlist input a storage node leads to: a PE input port, or the netlist
    register (delay) it is / reaches first. -> ("pe", (x, y), k, width) | ("reg", instance)
    (PE_input_width_<width>_num_<k>: dataK, or bitK when width is 1)"""
    seen = set()
    while True:
        if node[0] == "PORT" and node[1].startswith("PE_input"):
            w = re.match(r"PE_input_width_(\d+)_num_(\d+)$", node[1])
            return ("pe", (node[2], node[3]), int(w.group(2)), int(w.group(1)))
        if node[0] == "REG":
            inst = m.netreg.get((node[2], node[3], node[1]))
            # a register of the pre-PnR netlist (not one PnR pipelining added)
            if inst and not inst.startswith(("pnr_pipelining", "rv_balance")):
                return ("reg", inst)
        cons = [c for c in m.fanout.get(node, []) if not m.is_sink(c)]
        if len(cons) != 1 or node in seen:
            return None
        seen.add(node)
        node = cons[0]


def plan_by_instance(m, plan):
    """{"<instance>.<port>": regs} for rv_balance_branches.py --plan."""
    out = {}
    for sink, k in plan.items():
        if sink[0] == "pe":
            port = "bit" if len(sink) > 3 and sink[3] == 1 else "data"
            key = f"{m.pe_kind[sink[1]]}.{port}{sink[2]}"
        else:
            key = f"{sink[1]}.in"
        out[key] = out.get(key, 0) + k
    return out


def insert_stages(m, node, k):
    """Put k register stages (reg_depth each, empty) in front of storage node `node`
    on every producer edge that feeds it (as padding registers on that netlist edge)."""
    if k <= 0:
        return
    for p, cons in list(m.fanout.items()):
        if node in cons:
            base = sum(1 for n in m.cap if n[0] == "PAD" and n[1] == f"{node}")
            chain = [("PAD", f"{node}", p, base + i) for i in range(k)]
            for c in chain:
                m.cap[c] = m.reg_depth
                m.init[c] = 0
            m.fanout[p] = [chain[0] if c == node else c for c in cons]
            for a, b in zip(chain, chain[1:]):
                m.fanout[a] = [b]
            m.fanout[chain[-1]] = [node]


def model_of(bin_dir, **kw):
    return Model(f"{bin_dir}/design.route", f"{bin_dir}/design.place", f"{bin_dir}/design_top.json", **kw)


def placement_of(bin_dir):
    """Pinnable placement of a PnR result (for manual.place): {block id: (x, y)} of every
    non-register block and {instance name: (x, y)} of every netlist register (the
    registers PnR pipelining adds are left free: they are not in the netlist)."""
    out = {}
    for line in open(f"{bin_dir}/design.place").read().splitlines()[2:]:
        w = line.split()
        if len(w) < 4 or not w[-1].startswith("#"):
            continue
        xy = (int(w[-3]), int(w[-2]))
        if not w[-1].startswith("#r"):
            out[w[-1][1:]] = xy
        elif not w[0].startswith("pnr_pipelining"):
            out[w[0].split("@")[0]] = xy
    return out


def arrivals(m):
    """Arrival of each storage node's tokens in FIFO stages from the sources (MEM
    outputs, input IO = 0): a stage adds 1 (an enabled primitive output FIFO 1 more);
    a netlist register's pre-filled tokens subtract theirs (its output pairs with
    tokens that entered init cycles earlier); PE cores join their inputs (max).
    Constant-fed nodes are None."""
    pred = defaultdict(list)
    for p, cons in m.fanout.items():
        for c in cons:
            pred[c].append(p)
    for xy, pe in m.pes.items():
        for o in pe["out"]:
            pred[o].extend(pe["in"])
    memo = {}

    def arr(n, stack=()):
        if n in memo:
            return memo[n]
        if m.is_source(n):
            a = 0
        elif m.const_out(n) or n in stack:
            a = None
        else:
            ps = [arr(p, stack + (n,)) for p in pred.get(n, [])]
            ps = [x for x in ps if x is not None]
            prim = n[0] == "PORT" and n[1].startswith("PE_output") and (n[2], n[3]) in m.prim_out
            a = (max(ps) + 1 + prim - m.init.get(n, 0)) if ps else None
        memo[n] = a
        return a
    for n in list(m.cap):
        arr(n)
    return memo


def mismatches(m, arr=None):
    """[(PE input node, stages it arrives before the PE's latest input)] over the
    non-constant inputs of every PE with two or more of them, except the unpaddable ones
    (Model.unpaddable: an in-tile core-to-core wire, a loop through a memory): they count
    for the latest input, but no padding goes on them, so they are left early (see
    early_unpaddable)."""
    arr = arrivals(m) if arr is None else arr
    out = []
    for xy, pe in m.pes.items():
        if m.const_pe(xy):
            continue
        ins = [(i, arr.get(i)) for i in pe["in"] if arr.get(i) is not None]
        if len(ins) > 1:
            top = max(a for _, a in ins)
            out += [(i, top - a) for i, a in ins if not m.unpaddable(i)]
    return out


def early_unpaddable(m, arr=None):
    """[(PE input node, stages early)] of the inputs mismatches() leaves out
    (Model.unpaddable) that arrive early."""
    arr = arrivals(m) if arr is None else arr
    out = []
    for xy, pe in m.pes.items():
        if m.const_pe(xy):
            continue
        ins = [(i, arr.get(i)) for i in pe["in"] if arr.get(i) is not None]
        if len(ins) > 1:
            top = max(a for _, a in ins)
            out += [(i, top - a) for i, a in ins if m.unpaddable(i) and top > a]
    return out


def unique_stages(m, node):
    """Register stages on the part of the route into `node` that no other sink shares:
    walk back while the predecessor feeds only this path; stop at a fork, a source, a
    PE or an original netlist register (pipelining and padding registers count)."""
    pred = defaultdict(list)
    for p, cons in m.fanout.items():
        for c in cons:
            pred[c].append(p)
    n, count = node, 0
    while True:
        ps = pred.get(n, [])
        if len(ps) != 1:
            return count
        p = ps[0]
        if p[0] != "REG" or len(m.fanout.get(p, [])) != 1:
            return count
        inst = m.netreg.get((p[2], p[3], p[1]))
        if inst and not inst.startswith(("pnr_pipelining", "rv_balance")):
            return count
        count += 1
        n = p


def balance_plan_abs(m):
    """Latency matching as absolute padding: every route hop already has a register
    (EXHAUSTIVE_PIPE), so a padding register only adds latency when the edge needs more
    registers than its route has hops. For each PE input arriving d stages early:
    registers on its edge = the stages on its unshared route now + d.
    -> {netlist sink: registers}"""
    plan = {}
    for i, d in mismatches(m):
        if d > 0:
            sink = netlist_sink(m, i)
            if sink is not None:
                plan[sink] = unique_stages(m, i) + d
    return plan


def latency_match_plan(m, max_rounds=10):
    """Latency matching for a design WITHOUT PnR pipelining (no EXHAUSTIVE_PIPE): route
    hops are wires there, so a PE input arriving d stages early gets exactly d padding
    registers (no parity constraint, no absolute count). Iterated in the model until no
    join mismatches, since padding one join shifts the arrivals downstream. Adds the
    stages to m. -> {netlist sink: registers}"""
    plan = {}
    for _ in range(max_rounds):
        mm = [(i, d) for i, d in mismatches(m) if d > 0]
        if not mm:
            break
        for i, d in mm:
            sink = netlist_sink(m, i)
            plan[sink] = plan.get(sink, 0) + d
            insert_stages(m, i, d)
    return plan


def min_register_plan(m):
    """Latency matching with the fewest padding registers, for a design WITHOUT PnR
    pipelining, as an LP (scipy HiGHS). Each producer p (PE output, MEM output, input IO,
    netlist register) gets one padding chain of m(p) registers that its consumers share:
    consumer c taps it at position pad(p, c), so the chain costs max_c pad(p, c), not
    the sum. A PE may also start later than its earliest input allows, which moves
    padding off shared edges (retiming). Variables: t(PE) = arrival at its matched input
    FIFOs, a(r) per netlist register, m(p). Constraints: pad(p, c) = a(c) - a(p) - 1 +
    init(c) >= 0 on edges into PE inputs and netlist registers (== 0 elsewhere), every
    non-constant input of a PE at t(PE), its outputs at t(PE) + 1 (+1 with the primitive
    output FIFO), sources at 0. An edge into an unpaddable input (Model.unpaddable)
    only needs pad >= 0 and is never padded: its input may stay early. Minimize sum
    m(p); the constraint matrix is a network
    matrix, so the optimum is integral. Falls back to latency_match_plan(m) when scipy
    is missing or the LP fails. Adds the stages to m.
    -> {netlist sink: registers}; consumers of one netlist driver share its chain
    (hooks/rv_balance_branches.py --share)"""
    try:
        import numpy as np
        from scipy.optimize import linprog
        from scipy.sparse import lil_matrix
    except ImportError:
        return latency_match_plan(m)
    arr = arrivals(m)
    pe_of = {n: xy for xy, pe in m.pes.items() for n in pe["in"] + pe["out"]}
    var = {}

    def v(key):
        return var.setdefault(key, len(var))

    def a_expr(n):
        # arrival of node n as ({variable: coefficient}, constant)
        if m.is_source(n) or m.const_out(n):
            return {}, 0
        if n[0] == "PORT" and n[1].startswith("PE_input"):
            return {v(("t", pe_of[n])): 1}, 0
        if n[0] == "PORT" and n[1].startswith("PE_output"):
            return {v(("t", pe_of[n])): 1}, 1 + (pe_of[n] in m.prim_out) - m.init.get(n, 0)
        return {v(("a", n)): 1}, 0

    def is_netreg(n):
        inst = n[0] == "REG" and m.netreg.get((n[2], n[3], n[1]))
        return bool(inst) and not inst.startswith(("pnr_pipelining", "rv_balance"))
    edges = []   # (producer, consumer, "pad" | "slack" (early allowed, never padded) | "eq")
    for p, cons in m.fanout.items():
        if (p[0] == "PORT" and p[1].startswith("PE_input")) or (arr.get(p) is None and not m.is_source(p)):
            continue
        for c in cons:
            if not m.is_sink(c) and arr.get(c) is not None:
                pe_in = c[0] == "PORT" and c[1].startswith("PE_input")
                kind = "slack" if m.unpaddable(c) else "pad" if pe_in or is_netreg(c) else "eq"
                edges.append((p, c, kind))
    ub, ub_rhs, eq, eq_rhs = [], [], [], []
    for p, c, kind in edges:
        (ce, cc), (pe_, pc) = a_expr(c), a_expr(p)
        expr = defaultdict(float)
        for k, x in ce.items():
            expr[k] += x
        for k, x in pe_.items():
            expr[k] -= x
        const = cc - pc - 1 + m.init.get(c, 0)   # pad = expr + const
        if kind == "slack":
            ub.append({k: -x for k, x in expr.items()})      # pad >= 0, never realized
            ub_rhs.append(const)
        elif kind == "pad":
            ub.append({k: -x for k, x in expr.items()})      # pad >= 0
            ub_rhs.append(const)
            row = dict(expr)                                  # pad <= m(p)
            row[v(("m", p))] = row.get(v(("m", p)), 0) - 1
            ub.append(row)
            ub_rhs.append(-const)
        else:
            eq.append(dict(expr))
            eq_rhs.append(-const)
    if not ub:
        return {}

    def matrix(rows):
        a = lil_matrix((len(rows), len(var)))
        for r, row in enumerate(rows):
            for k, x in row.items():
                a[r, k] = x
        return a.tocsr()
    cost = np.zeros(len(var))
    for key, i in var.items():
        cost[i] = 1.0 if key[0] == "m" else 0.0
    res = linprog(cost, A_ub=matrix(ub), b_ub=np.array(ub_rhs, float),
                  A_eq=matrix(eq) if eq else None, b_eq=np.array(eq_rhs, float) if eq else None,
                  bounds=[(0, None)] * len(var), method="highs")
    if res.status != 0:
        return latency_match_plan(m)
    x = np.round(res.x).astype(int)

    def value(n):
        e, c0 = a_expr(n)
        return int(sum(x[k] * cf for k, cf in e.items()) + c0)
    pads = [(c, value(c) - value(p) - 1 + m.init.get(c, 0)) for p, c, kind in edges if kind == "pad"]
    plan = {}
    for c, d in pads:
        if d > 0:
            sink = netlist_sink(m, c)
            plan[sink] = plan.get(sink, 0) + d
            insert_stages(m, c, d)
    if any(d > 0 for _, d in mismatches(m)):
        raise RuntimeError("min_register_plan: joins still mismatched after the LP plan")
    return plan


def parity_outfifo(m, max_pes=6):
    """Route padding between pinned endpoints changes an edge's stage count by an even
    number only (every hop has a register; Manhattan path lengths between two tiles
    share their parity), so an odd mismatch at a join can never be padded away.
    Choose the set of PEs whose primitive output FIFO to enable (+1 stage each) so that
    every remaining mismatch is even: fewest odd mismatches, then smallest total, then
    fewest PEs, over every set of at most max_pes PEs (exhaustive: fine for a few dozen
    PEs at max_pes 6). Applies it to m (m.prim_out). -> [PE instance]"""
    pes = sorted(xy for xy in m.pes if not m.const_pe(xy) and m.pes[xy]["out"])
    best = None
    for k in range(min(len(pes), max_pes) + 1):
        for combo in combinations(pes, k):
            m.prim_out = set(combo)
            mm = mismatches(m)
            key = (sum(d % 2 for _, d in mm), sum(d for _, d in mm), k)
            if best is None or key < best[0]:
                best = (key, combo)
    m.prim_out = set(best[1])
    return sorted(m.pe_kind[xy] for xy in m.prim_out)


def outfifo_config(names):
    """PE_fifos_bypass_config.json entries keeping these PEs' primitive output FIFO."""
    return {n: {"input_fifo_bypass": [0, 0, 0], "output_fifo_bypass": 0, "prim_outfifo_bypass": 0}
            for n in names}


def apply_outfifo(m, names):
    xy_of = {name: xy for xy, name in m.pe_kind.items()}
    m.prim_out = {xy_of[n] for n in names}


if __name__ == "__main__":
    m = model_of(sys.argv[1])
    rate, _ = m.run(6000, 1500)
    print(f"modelled rate {rate:.3f}")
    if rate < 0.995:
        outfifo = parity_outfifo(m)
        plan = balance_plan_abs(m)
        print(f"next round: PE output FIFOs {outfifo}, padding ({sum(plan.values())} registers):")
        print(json.dumps(plan_by_instance(m, plan), indent=1))
