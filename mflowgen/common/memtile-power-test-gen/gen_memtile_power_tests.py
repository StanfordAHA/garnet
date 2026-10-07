#!/usr/bin/env python3
"""Idle + active power-test stimulus for one lake-spec MemCore tile.

Tile-level port of lake's standalone power tests (lake
pd/thesis/power-test-gen/gen_power_bitstreams.py, which drives a bare
`lakespec`). Here the DUT is the whole Tile_MemCore (SB/CB + config bus +
MemoryTileBuilder wrapper + spec), so every byte of configuration goes in
through the tile's own config bus, and data enters / leaves through the
tile's switch-box pins, exactly as on the CGRA.

Two variants, same tile, same routes, same stimulus -- only the spec program
differs, so active minus idle is the memory's own work. Programs and input
data come from lake.utils.power_test_programs, shared with the standalone
flow (same spec + seed -> same programs and input words):

- idle:   the EMPTY application (tile_en=1, lakespec mode, every port
          controller cleared): no port ever fires.
- active: the most traffic the spec can sustain -- static: every port streams
          one element per cycle where the memory keeps up, SRAM accesses
          slotted so the memory port(s) are busy every cycle, readers
          re-reading what their writers stored; RV: free-flowing writer ->
          reader streams (a barrier program on 1-D specs).
- stimulus: every spec input port is routed to switch-box tracks and fed a
          fresh random word every cycle from flush release (input_data.hex,
          from power_test_programs.input_streams), valids and readies high.

The CGRA is rebuilt in Python with the exact garnet.py flags the rtl step
used, so the routing-mux and core-register addresses are the ones in the
RTL being measured. Must run with cwd = the garnet checkout (Genesis paths).

Outputs (--outdir):
    testbench.idle.sv / testbench.active.sv   tb, module `testbench`, instance
                                              `dut` (config writes inlined)
    input_data.hex                            the random streams both tbs read
                                              (track-major, one word per cycle)
    power_tests.json                          tile, routes, input tracks,
                                              programs, config writes, window

Each testbench resets the tile with flush held high, writes the config,
releases flush (the spec's schedules start), then records switching activity
for `window` cycles into run.saif ($toggle_* tasks under VCS; under Xcelium
the testbench $stops at the window edges and the sim step's cmd.tcl dumpsaifs)
and prints `MEMTILE_POWER_TEST <variant> PASS|FAIL` from a self-check on the
tile outputs (idle: data outputs quiet; active: every routed output streams\nat least half the elements the program should deliver in the window).
"""

import argparse
import functools
import json
import os
import re
import sys


def _power_test_programs():
    """Idle/active programs + input streams, shared with lake's standalone
    power tests (one source of truth: same spec + seed -> same programs and
    the same input words in both flows)."""
    try:
        from lake.utils import power_test_programs
    except ImportError as e:
        raise SystemExit(f"*** ERROR: this lake has no lake/utils/power_test_programs.py "
                         f"({e}); it ships with lake THESIS alongside this step") from e
    return power_test_programs


# ---------------------------------------------------------------------------
# Garnet / tile plumbing
# ---------------------------------------------------------------------------
def build_garnet(garnet_flags):
    sys.path.insert(0, os.getcwd())
    sys.argv = ["garnet.py"] + garnet_flags
    import garnet as G
    args, io_sides = G.parse_args()
    # Same env propagation as garnet.py main() (create_cgra reads these).
    if args.lake_spec_config:
        os.environ["LAKE_SPEC_CONFIG"] = args.lake_spec_config
    if args.lake_spec_mode:
        os.environ["LAKE_SPEC_MODE"] = args.lake_spec_mode
    if getattr(args, "lake_pond_spec_config", None):
        os.environ["LAKE_POND_SPEC_CONFIG"] = args.lake_pond_spec_config
    return G.Garnet(args, io_sides)


def find_mem_tile(ic, want=None):
    from memory_core.core_combiner_core import CoreCombinerCore
    mems = sorted(loc for loc, t in ic.tile_circuits.items()
                  if isinstance(t.core, CoreCombinerCore) and t.core.pnr_tag in ("m", "M"))
    if not mems:
        raise SystemExit("*** ERROR: no MemCore tile in this CGRA")
    if want is not None:
        if want not in mems:
            raise SystemExit(f"*** ERROR: tile {want} is not a MemCore tile; MEM tiles: {mems}")
        return want
    return mems[0]


def spec_controller(core):
    for c in core.dut.controllers:
        if c.get_config_mode_str() == "lakespec" and hasattr(c, "spec"):
            return c
    raise SystemExit("*** ERROR: the MemCore has no lake-spec controller "
                     "(was the RTL built with --lake-spec-config?)")


def spec_port_pins(core, idx):
    """Tile core pins of spec port idx, from the MemCore's lakespec port remap.
    A 16-bit spec port is one 17-bit pin (comply_17: data + an unused MSB);
    any other data width is bit-blasted onto 1-bit pins `port_<i>_<bit>`
    (MSB = the unused comply_17 bit) with its own 1-bit `port_<i>_valid` /
    `port_<i>_ready` pins."""
    remap = core.get_port_remap()["lakespec"]
    bits, word, valid, ready = {}, [], None, None
    for k, v in remap.items():
        m = re.fullmatch(rf"port_{idx}(?:_(.*))?", k)
        if not m:
            continue
        suf = m.group(1) or ""
        if suf.isdigit():
            bits[int(suf)] = v
        elif suf == "valid":
            valid = v
        elif suf == "ready":
            ready = v
        else:
            word.append(v)
    if len(word) == 1 and not bits:
        return {"data": word, "unused_msb": False, "valid": valid, "ready": ready}
    if bits and not word:
        return {"data": [bits[b] for b in sorted(bits)], "unused_msb": True,
                "valid": valid, "ready": ready}
    raise SystemExit(f"*** ERROR: cannot read spec port {idx} pins from {remap}")


def _pin_width(pin):
    return int(re.search(r"_width_(\d+)_", pin).group(1))


IN_SIDES = ("WEST", "NORTH", "SOUTH", "EAST")
OUT_SIDES = ("EAST", "NORTH", "SOUTH", "WEST")


def _ordered(nodes, sides):
    return sorted(nodes, key=lambda n: (sides.index(n.side.name), n.track))


def plan_routes(ic, x, y, in_ports, out_ports):
    """Route every spec port of the tile to switch-box tracks.

    Inputs take SB_IN tracks in WEST, NORTH, SOUTH, EAST order (16-bit port k
    -> WEST track k). Data pins get their own random track while tracks last,
    then share them (a 32-bit port bit-blasted onto 1-bit pins needs more than
    the 20 1-bit tracks: shared bits are correlated but all toggle). 1-bit
    valid/ready pins share one track held at 1; unused MSB pins one quiet
    track. Outputs take SB_OUT tracks in EAST, NORTH, SOUTH, WEST order,
    interleaving the ports bit by bit, pipeline register bypassed; data bits
    beyond the free tracks stay unobserved.

    Returns (routes, drive {SB_IN pin: 'rand'|'one'}, observed {SB_OUT pin:
    width}, source {random SB_IN pin: (spec port name, bit or None)} -- the
    port word (None: the whole word, on a 17-bit track) or word bit the track
    carries; a shared track carries its first pin's bit)."""
    from canal.cyclone import SwitchBoxIO, RegisterMuxNode
    tiles = {w: ic.get_graph(w).get_tile(x, y) for w in (1, 17)}
    routes, drive, observed, source = {}, {}, {}, {}

    def route_in(src, pin):
        node = tiles[_pin_width(pin)].ports[pin]
        assert src in node.get_conn_in(), f"{src} cannot reach {pin}"
        routes[f"in_{pin}"] = [[src, node]]

    rand_pins, one_pins, zero_pins, pin_source = [], [], [], {}
    for name, p in in_ports:
        data = p["data"]
        rand = data[:-1] if p["unused_msb"] else data
        rand_pins += rand
        pin_source.update({q: (name, b if p["unused_msb"] else None) for b, q in enumerate(rand)})
        zero_pins += data[-1:] if p["unused_msb"] else []
        one_pins += [p["valid"]] if p["valid"] else []
    for _, p in out_ports:
        one_pins += [p["ready"]] if p["ready"] else []

    for w in (17, 1):
        rands = [q for q in rand_pins if _pin_width(q) == w]
        ones = [q for q in one_pins if _pin_width(q) == w]
        zeros = [q for q in zero_pins if _pin_width(q) == w]
        if not (rands or ones or zeros):
            continue
        pool = _ordered([n for n in tiles[w].switchbox.get_all_sbs()
                         if n.io == SwitchBoxIO.SB_IN], IN_SIDES)
        quiet = pool.pop() if zeros else None
        one = pool.pop() if ones else None
        assert pool or not rands, f"no {w}-bit tracks left for data"
        for i, q in enumerate(rands):
            src = pool[i % len(pool)]
            route_in(src, q)
            drive[str(src)] = "rand"
            source.setdefault(str(src), pin_source[q])
        for q in ones:
            route_in(one, q)
            drive[str(one)] = "one"
        for q in zeros:
            route_in(quiet, q)

    lists = [p["data"][:-1] if p["unused_msb"] else p["data"] for _, p in out_ports]
    used = set()
    for b in range(max((len(l) for l in lists), default=0)):
        for pins in lists:
            if b >= len(pins):
                continue
            pin = pins[b]
            node = tiles[_pin_width(pin)].ports[pin]
            free = _ordered([n for n in node if getattr(n, "io", None) == SwitchBoxIO.SB_OUT
                             and str(n) not in used], OUT_SIDES)
            if not free:
                continue
            sb = free[0]
            rmux = [n for n in sb if isinstance(n, RegisterMuxNode)]
            assert len(rmux) == 1, f"no register mux after {sb}"
            routes[f"out_{pin}"] = [[node, sb, rmux[0]]]
            used.add(str(sb))
            observed[str(sb)] = _pin_width(pin)
    return routes, drive, observed, source


def track_streams(source, streams, width):
    """{random SB_IN pin: per-cycle values}: the spec port's random words
    (lake power_test_programs.input_streams) on a word track, masked to the
    16 data bits (bit 16 is the unused comply_17 bit), or one bit of them on
    a 1-bit track."""
    out = {}
    for pin, (port, bit) in source.items():
        words = streams[port]
        if bit is None:
            out[pin] = [w & ((1 << min(width[pin], 16)) - 1) for w in words]
        else:
            out[pin] = [(w >> bit) & 1 for w in words]
    return out


def quiet_unused_muxes(ic, x, y, drive, routes):
    """Point every unused switch-box output and connection box whose default
    (select 0) source carries a random stream at a static source instead --
    an undriven track, else the track held at 1 -- so the stimulus only
    reaches what it is routed to (garnet's bitstreams likewise steer unused
    muxes away from live tracks: archipelago.power.reduce_switching). Select
    only: on a ready-valid tile a route config also turns on the mux's
    valid/ready `_enable`, which an unused mux must not get.

    Returns (config writes, muxes left on a random source because every
    source they have is one)."""
    from canal.cyclone import SwitchBoxIO, PortNode
    tile_circuit = ic.tile_circuits[(x, y)]
    used = {str(seg[i]) for segs in routes.values() for seg in segs for i in range(1, len(seg))}
    cfg, stuck = [], []
    for width in (1, 17):
        tile = ic.get_graph(width).get_tile(x, y)
        muxes = [n for n in tile.switchbox.get_all_sbs() if n.io == SwitchBoxIO.SB_OUT]
        muxes += list(tile.ports.values())   # CBs (core outputs have no sources)
        for node in muxes:
            srcs = node.get_conn_in()
            if str(node) in used or len(srcs) < 2 or drive.get(str(srcs[0])) != "rand":
                continue
            quiet = sorted((s for s in srcs if drive.get(str(s)) != "rand"
                            and not isinstance(s, PortNode)),
                           key=lambda s: str(s) in drive)   # undriven first
            if not quiet:
                stuck.append(str(node))
                continue
            entry = tile_circuit.get_route_bitstream_config(quiet[0], node)
            reg_addr, feat_addr, data = entry[0] if isinstance(entry, list) else entry
            cfg.append((ic.get_config_addr(reg_addr, feat_addr, x, y), data))
    return cfg, stuck


def gen_config(ic, x, y, core, smc, app, routes, quiet):
    """(addr, data) writes for one variant, merged per address the way
    garnet's bitstream generation does (gemstone compress_config_data)."""
    from gemstone.common.util import compress_config_data
    spec = smc.spec
    orig = spec.gen_bitstream
    # The MemoryTileBuilder hands the controller's config straight to
    # Spec.gen_bitstream(); ours is already a port-level program, so take the
    # same `over` path the standalone flow uses (no clockwork rewrite).
    spec.gen_bitstream = functools.partial(orig, over=True)
    try:
        core_cfg = ic.configure_placement(x, y, {"mode": "lake", "config": app},
                                          node_name="memtile_power_test",
                                          pnr_tag=core.pnr_tag, node_num=0)
    finally:
        spec.gen_bitstream = orig
    route_cfg = ic.get_route_bitstream(routes) if routes else []
    return compress_config_data(route_cfg + quiet + core_cfg, skip_zero=False)


# ---------------------------------------------------------------------------
# Testbench
# ---------------------------------------------------------------------------
PORT_RE = re.compile(r"^\s*(input|output|inout)\s+(?:wire\s+|logic\s+|reg\s+)?"
                     r"(?:\[(\d+):(\d+)\]\s*)?(\w+)\s*,?\s*$")


def tile_pins_from_rtl(design_v, module="Tile_MemCore"):
    """[(direction, width, name)] from the ANSI port list of `module`."""
    pins, inside = [], False
    head = re.compile(rf"^\s*module\s+{module}\s*\(")
    with open(design_v, errors="replace") as f:
        for line in f:
            if not inside:
                inside = bool(head.match(line))
                continue
            if line.strip().startswith(");"):
                break
            m = PORT_RE.match(line)
            if m:
                d, hi, lo, name = m.groups()
                w = int(hi) - int(lo) + 1 if hi is not None else 1
                pins.append((d, w, name))
    if not pins:
        raise SystemExit(f"*** ERROR: no `module {module} (` port list in {design_v}")
    return pins


def write_testbench(path, variant, pins, cfg, tile_id, window, drive, rand, n_stream,
                    expect, clock_period):
    """drive: {SB_IN pin: 'rand' (input stream) | 'one' (held at 1)}; rand:
    the 'rand' pins in input_data.hex order; n_stream: words per track in it;
    expect: {SB_OUT pin: minimum value changes in the window} (active only;
    idle checks every switch-box data output stays quiet)."""
    names = {n for _, _, n in pins}
    for n in list(drive) + list(expect):
        assert n in names, f"pin {n} not on the tile"
    rv_in = [f"{n}_valid" for n in drive if f"{n}_valid" in names]
    rv_out = [f"{n}_ready" for n in expect if f"{n}_ready" in names]
    width = {n: w for _, w, n in pins}
    data_outs = [n for d, w, n in pins if d == "output" and re.match(r"SB_T\d+_\w+_SB_OUT_B\d+$", n)]

    L = []
    w = L.append
    w(f"// Generated by gen_memtile_power_tests.py -- {variant} power test for Tile_MemCore.")
    w("`timescale 1ns/1ps")
    w("`ifndef CLK_PERIOD")
    w(f"`define CLK_PERIOD {clock_period}")
    w("`endif")
    w("module testbench;")
    w(f"    localparam integer WINDOW = {window};")
    w(f"    localparam integer N_CFG = {len(cfg)};")
    w("    localparam real D = `CLK_PERIOD * 0.2;  // drive inputs after the edge (gate-level safe)")
    w("")
    w("    reg clk = 1'b0;")
    w("    always #(`CLK_PERIOD / 2.0) clk = ~clk;")
    w("")
    for d, wd, n in pins:
        if n == "clk":
            continue
        rng = f"[{wd - 1}:0] " if wd > 1 else ""
        if d == "input":
            w(f"    reg  {rng}{n} = '0;")
        else:
            w(f"    wire {rng}{n};")
    w("")
    w("    Tile_MemCore dut (")
    w(",\n".join(f"        .{n}({n})" for _, _, n in pins))
    w("    );")
    w("")
    w("    reg [31:0] cfg_addr [0:N_CFG > 0 ? N_CFG - 1 : 0];")
    w("    reg [31:0] cfg_data [0:N_CFG > 0 ? N_CFG - 1 : 0];")
    w("    initial begin")
    for i, (a, dt) in enumerate(cfg):
        w(f"        cfg_addr[{i}] = 32'h{a:08x}; cfg_data[{i}] = 32'h{dt:08x};")
    w("    end")
    w("")
    w("    // Stimulus: the random input streams, the same for idle and active")
    w("    // (inputs/input_data.hex, track-major: word k*N_STREAM + t is track k's")
    w("    // value in cycle t after flush release; lake power_test_programs).")
    w(f"    localparam integer N_STREAM = {n_stream};")
    w(f"    localparam integer N_TRACKS = {max(len(rand), 1)};")
    w("    reg [16:0] stim [0:N_TRACKS * N_STREAM - 1];")
    if rand:
        w("    initial $readmemh(\"inputs/input_data.hex\", stim);")
    w("    reg stim_on = 1'b0;")
    w("    integer t = 0;")
    w("    always @(posedge clk) if (stim_on) begin")
    w("        t = t + 1;")
    for k, n in enumerate(rand):
        w(f"        {n} <= #(D) stim[{k} * N_STREAM + (t % N_STREAM)];")
    w("    end")
    w("")
    w("    // Output activity (value changes) on every switch-box data output.")
    for n in data_outs:
        w(f"    integer chg_{n} = 0;")
    for n in data_outs:
        wd = width[n]
        rng = f"[{wd - 1}:0] " if wd > 1 else ""
        w(f"    reg {rng}prev_{n};")
        w(f"    always @(posedge clk) prev_{n} <= {n};")
    w("    reg counting = 1'b0;")
    w("    always @(posedge clk) if (counting) begin")
    for n in data_outs:
        w(f"        if ({n} !== prev_{n}) chg_{n} = chg_{n} + 1;")
    w("    end")
    w("")
    w("    integer i, fails;")
    w("    initial begin")
    w("        reset = 1'b1;")
    w("        flush = 1'b1;   // held through config, like the lake standalone tb")
    w("        stall = 1'b0;")
    w(f"        tile_id = 16'h{tile_id:04x};")
    w("        repeat (4) @(posedge clk);")
    w("        #(D) reset = 1'b0;")
    w("        repeat (2) @(posedge clk);")
    w("        for (i = 0; i < N_CFG; i = i + 1) begin")
    w("            @(posedge clk);")
    w("            #(D);")
    w("            config_config_addr = cfg_addr[i];")
    w("            config_config_data = cfg_data[i];")
    w("            config_write = 1'b1;")
    w("        end")
    w("        @(posedge clk);")
    w("        #(D);")
    w("        config_write = 1'b0;")
    w("        config_config_addr = '0;")
    w("        config_config_data = '0;")
    w("        repeat (4) @(posedge clk);")
    w("        // Release flush: the spec's schedules start here.")
    w("        #(D);")
    w("        flush = 1'b0;")
    for n in sorted(rv_in + rv_out + [k for k, v in drive.items() if v == "one"]):
        w(f"        {n} = 1'b1;")
    for k, n in enumerate(rand):
        w(f"        {n} = stim[{k} * N_STREAM];")
    w("        stim_on = 1'b1;")
    w("        @(posedge clk);")
    w("        counting = 1'b1;")
    w("        // SAIF over the window only. Xcelium has no $toggle_* tasks: the")
    w("        // sim step's cmd.tcl runs `dumpsaif` between these two $stops.")
    w("`ifdef MEMTILE_SAIF_TCL")
    w("        $stop;")
    w("`else")
    w("        $set_toggle_region(testbench.dut);")
    w("        $toggle_start();")
    w("`endif")
    w("        repeat (WINDOW) @(posedge clk);")
    w("`ifdef MEMTILE_SAIF_TCL")
    w("        $stop;")
    w("`else")
    w("        $toggle_stop();")
    w("        $toggle_report(\"run.saif\", 1.0e-9, \"testbench\");")
    w("`endif")
    w("        counting = 1'b0;")
    w("        fails = 0;")
    if variant == "idle":
        w("        // Idle: same stimulus, empty program -> the memory moves nothing,")
        w("        // so every switch-box data output must stay quiet.")
        for n in data_outs:
            w(f"        if (chg_{n} > 0) begin fails = fails + 1; "
              f"$display(\"MEMTILE_POWER_TEST idle: {n} changed %0d times\", chg_{n}); end")
    else:
        w("        // Active: every routed output must keep moving (reads from the SRAM).")
        for n in sorted(expect):
            w(f"        $display(\"MEMTILE_POWER_TEST active: {n} changed %0d times in %0d cycles\", chg_{n}, WINDOW);")
            w(f"        if (chg_{n} < {expect[n]}) fails = fails + 1;")
    w(f"        if (fails == 0) $display(\"MEMTILE_POWER_TEST {variant} PASS window=%0d\", WINDOW);")
    w(f"        else $display(\"MEMTILE_POWER_TEST {variant} FAIL (%0d checks)\", fails);")
    w("        $finish;")
    w("    end")
    w("endmodule")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--design-v", required=True,
                    help="tile RTL from the rtl step (Tile_MemCore pin list)")
    ap.add_argument("--sim-cycles", type=int, default=1000,
                    help="measurement window in cycles (shortened if the spec cannot keep "
                         "its ports busy that long; see power_tests.json `window`)")
    ap.add_argument("--clock-period", type=float, default=1.0, help="ns, default for `CLK_PERIOD")
    ap.add_argument("--tile", help="X,Y of the MEM tile to configure (default: first MEM tile)")
    ap.add_argument("--seed", type=int, default=1,
                    help="input data seed (lake's standalone power tests use the same "
                         "streams for the same seed)")
    ap.add_argument("--variants", default="idle,active")
    ap.add_argument("garnet_flags", nargs=argparse.REMAINDER,
                    help="-- followed by the garnet.py flags the rtl step used")
    a = ap.parse_args()
    flags = [f for f in a.garnet_flags if f != "--"]
    flags = [f for f in flags if f not in ("-v", "--verilog")]

    ptp = _power_test_programs()
    g = build_garnet(flags)
    ic = g.interconnect
    want = tuple(int(v) for v in a.tile.split(",")) if a.tile else None
    x, y = find_mem_tile(ic, want)
    core = ic.tile_circuits[(x, y)].core
    smc = spec_controller(core)
    spec = smc.spec
    spec_cfg = {}
    if os.environ.get("LAKE_SPEC_CONFIG"):
        with open(os.environ["LAKE_SPEC_CONFIG"]) as f:
            spec_cfg = json.load(f)
    mode = os.environ.get("LAKE_SPEC_MODE", "static") or "static"
    n_in = spec_cfg.get("in_ports", 2)
    n_out = spec_cfg.get("out_ports", 2)
    dw = spec_cfg.get("data_width", 16)
    active = ptp.active_program(spec, n_in, n_out, spec_cfg.get("vec_width", 4), dw,
                                spec_cfg.get("storage_capacity", 4096),
                                bool(spec_cfg.get("dual_port", False)), a.sim_cycles)
    window = active["window"]

    # Routes and stimulus are shared by both variants; only the program differs.
    in_ports = [(f"port_w{i}", spec_port_pins(core, spec.port_name_to_int(f"port_w{i}")))
                for i in range(n_in)]
    out_ports = [(f"port_r{j}", spec_port_pins(core, spec.port_name_to_int(f"port_r{j}")))
                 for j in range(n_out)]
    routes, drive, observed, source = plan_routes(ic, x, y, in_ports, out_ports)
    quiet, unquieted = quiet_unused_muxes(ic, x, y, drive, routes)
    pins = tile_pins_from_rtl(a.design_v)
    n_stream = ptp.stream_length(window)
    tracks = track_streams(source, ptp.input_streams(a.seed, n_in, n_stream, dw),
                           {n: w for _, w, n in pins})
    rand = sorted(tracks)

    os.makedirs(a.outdir, exist_ok=True)
    with open(os.path.join(a.outdir, "input_data.hex"), "w") as f:
        for pin in rand:
            f.writelines(f"{v:05x}\n" for v in tracks[pin])
    meta = {"tile": [x, y], "tile_id": ic.get_tile_id(x, y), "runtime_mode": mode,
            "spec_config": spec_cfg, "rv_spec": bool(spec.any_rv_sg),
            "requested_cycles": a.sim_cycles, "window": window, "seed": a.seed,
            "stream_length": n_stream, "driven_inputs": drive,
            "input_tracks": {pin: list(source[pin]) for pin in rand},
            "routes": {k: [[str(n) for n in seg] for seg in v] for k, v in routes.items()},
            "unquieted_muxes": unquieted, "variants": {}}

    for variant in [v.strip() for v in a.variants.split(",") if v.strip()]:
        if variant == "idle":
            app, expect = ptp.idle_program(), {}
        elif variant == "active":
            # A 1-bit output changes on about half the elements a word output does.
            m = active["min_output_changes"]
            app = active["app"]
            expect = {o: (m if w > 1 else max(1, m // 4)) for o, w in observed.items()}
        else:
            raise SystemExit(f"*** ERROR: unknown variant {variant}")
        cfg = gen_config(ic, x, y, core, smc, app, routes, quiet)
        tb = os.path.join(a.outdir, f"testbench.{variant}.sv")
        write_testbench(tb, variant, pins, cfg, ic.get_tile_id(x, y), window, drive, rand,
                        n_stream, expect, a.clock_period)
        meta["variants"][variant] = {
            "observed_outputs": expect,
            "program": json.loads(json.dumps(app, default=str)),
            "config": [[f"0x{ad:08x}", f"0x{dt:08x}"] for ad, dt in cfg]}
        print(f"{variant}: {len(cfg)} config writes, window {window} cycles, "
              f"{len(drive)} driven inputs ({len(rand)} random streams), "
              f"{len(observed)} observed outputs -> {tb}", file=sys.stderr)
    with open(os.path.join(a.outdir, "power_tests.json"), "w") as f:
        json.dump(meta, f, indent=2, default=str)


if __name__ == "__main__":
    main()
