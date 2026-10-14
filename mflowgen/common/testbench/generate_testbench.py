import os
import csv
import json
import re
from defines import inputs, outputs, scope
import subprocess

# A lake-spec app bundle (application step, app_bundle param) records the scope of
# the tiles in its run.vcd, the clock to sample on, and each tile design's ports
# (taken from the garnet.v the app ran on). Without one, the historical
# Interconnect_tb scope and the fixed port lists in defines.py apply.
CLOCK_PORTS = ("clk", "clk_pass_through")
CLOCK_OUT_PORTS = ("clk_out", "clk_pass_through_out_bot", "clk_pass_through_out_right")
clock_template = "Interconnect_tb.clk"
app_bundle = False

# App replays drive each input when the tile's SDC says it arrives
# (Tile_{MemCore,PE}/constraints/common.tcl, onyx; a test checks these): the
# passthrough inputs at pt_i_delay, the rest at i_delay = a fraction of the
# period. A PnR netlist sees its clock ~0.2 ns after the testbench's edge (clock
# tree), so inputs driven earlier than STA assumed race it: the fixed 0.2 ns
# corrupted the RV MEM tile's config registers (hold) at PnR level on gf12.
PT_INPUT_PREFIXES = ("stall", "config_config_data", "config_config_addr", "config_read", "config_write",
                     "reset", "flush", "read_config_data_in")
PT_INPUT_DELAY_NS = 0.7
INPUT_DELAY_FRACTION = {"Tile_MemCore": 0.2, "Tile_PE": 0.3}
if os.path.exists("inputs/manifest.json"):
    manifest = json.load(open("inputs/manifest.json"))  # "{}" without a bundle
    app_bundle = bool(manifest)
    scope = manifest.get("scope", scope)
    clock_template = manifest.get("clock", clock_template)


def tile_ports(design):
    """(inputs, outputs, clock inputs) of the DUT: from the bundle if present."""
    all_ports = json.load(open("inputs/tile_ports.json")) if os.path.exists("inputs/tile_ports.json") else {}
    if design in all_ports:
        ports = all_ports[design]
        ins = [n for n, _ in ports["inputs"] if n not in CLOCK_PORTS]
        outs = [n for n, _ in ports["outputs"] if n not in CLOCK_OUT_PORTS]
        clks = [n for n, _ in ports["inputs"] if n in CLOCK_PORTS]
        return ins, outs, clks
    return inputs, outputs, None


def generate_raw(tile, inputs, outputs):
    sv = open('waveform_to_csv.sh', 'w')

    waveform = 'run'
    clock = clock_template.format(scope=scope, tile=tile)

    input_signals = ' '.join([f'-signal {scope}.{tile}.{i}' for i in inputs])
    output_signals = ' '.join([f'-signal {scope}.{tile}.{o}' for o in outputs])
    flags = [
        "-overwrite",
        "-xsub 0",
        "-timeunits ps",
        "-radix hex",
        "-64bit",
        "-notime",
        f"-expression \"{clock} == 1'b1\"",
    ]
    flag_string = ' '.join(flags)

    sv.write('#!/bin/bash\n')
    sv.write(f'mkdir -p outputs/tile_tbs/{tile}\n')
    sv.write(f'if [ ! -f {waveform}.trn ]; then\nsimvisdbutil inputs/{waveform}.vcd -sst2\nfi\n')
    sv.write(f'simvisdbutil {waveform}.trn {input_signals} -output raw_input.csv {flag_string}\n')
    sv.write(f'simvisdbutil {waveform}.trn {output_signals} -output raw_output.csv {flag_string}\n')
    sv.close()

    subprocess.run(['chmod', '+x', 'waveform_to_csv.sh'])
    subprocess.run(['./waveform_to_csv.sh'])


def convert_raw(signals, input_file, output_file):
    dim_pattern = re.compile("\w*\[(\d+):0\]")
    raw = open(input_file, "r")
    f = open(output_file, "w")

    data = list(csv.reader(raw, delimiter=','))
    headers = data[0]

    widths = {}
    col = {}
    for i, h in enumerate(headers):
        name = h.split('.')[-1]
        try:
            width = int(dim_pattern.match(name).groups()[0]) + 1
            name = name.replace(f'[{width-1}:0]', '')
            widths[name] = width
        except Exception:
            widths[name] = 1
        col[name] = i

    for c in range(1, len(data)):
        to_write = []
        for s in signals:
            value = data[c][col[s]]

            # append leading zeros to pad up to 16 bits (4 hex spaces)
            while len(value) % 4 != 0:
                value = "0" + value

            term = []
            for i in range(int((len(value) - 1) / 4) + 1):
                partial_value = value[i * 4:min((i + 1) * 4, len(value) + 1)]
                term.append(partial_value)
            term.reverse()
            for t in term:
                to_write.append(t)
        to_write.reverse()
        f.write('_'.join(to_write) + '\n')

    f.close()
    raw.close()

    num_test_vectors = len(data) - 1
    return num_test_vectors, widths


def create_testbench(design, inputs, outputs, input_widths, output_widths, num_test_vectors, clock_inputs=None,
                     hold_reset=False, sdc_inputs=False, stall_release=None):
    """hold_reset (app bundle replays): the recording starts from simulator
    zero-init, but a gate-level tile's flops are X until its first reset (gf12:
    every output X until then, and the MEM tile's SRAM clock, clk & the tile_en
    config flop, X at the first edge, which makes the macro model invalidate its
    whole array). So drive reset from time 0 until the first recorded reset and
    check outputs only from that cycle on; the state before it is undefined in
    hardware too.

    sdc_inputs (app bundle replays): drive the inputs at their SDC arrival
    times (PT_INPUT_DELAY_NS, INPUT_DELAY_FRACTION) instead of 0.2 ns.

    App bundle replays (hold_reset) with a stall input also get saif_window,
    which rises when the tile's recorded stall is first released: cmd.tcl dumps
    the SAIF from there, as it did by counting stall changes. The GLB stalls only
    the columns the app uses, so a tile elsewhere (an idle tile) records stall 0
    throughout; its window opens at stall_release, the vector where the design's
    other tiles are released (else at the app's first flush)."""
    pwr_aware = os.environ.get("PWR_AWARE") == "True"
    hold_reset = hold_reset and "reset" in inputs
    sdc_inputs = sdc_inputs and design in INPUT_DELAY_FRACTION

    def addr(i):
        """The vector index register that drives input i."""
        if not sdc_inputs:
            return 'test_vector_addr'
        return 'pt_addr' if i.startswith(PT_INPUT_PREFIXES) else 'in_addr'

    tb = open("testbench.sv", "w")

    # write defines
    tb.write(f'`timescale 1ns/1ps\n')                           # noqa
    tb.write(f'`define NUM_TEST_VECTORS {num_test_vectors}\n')  # noqa
    tb.write(f'`define ASSIGNMENT_DELAY 0.2 \n')                # noqa
    if sdc_inputs:
        tb.write(f'`define IN_ASSIGNMENT_DELAY ({INPUT_DELAY_FRACTION[design]} * `CLK_PERIOD)\n')
        tb.write(f'`define PT_ASSIGNMENT_DELAY {PT_INPUT_DELAY_NS}\n')
    tb.write(f'\n')                                             # noqa

    input_base = 0
    for i in inputs:
        tb.write(f'`define SLICE_{i.upper()} {input_widths[i]-1+input_base}:{input_base}\n')
        input_base += input_widths[i]
        if input_widths[i] % 16 != 0:
            input_base += (16 - input_widths[i] % 16)
    tb.write('\n')
    output_base = 0
    for o in outputs:
        tb.write(f'`define SLICE_{o.upper()} {output_widths[o]-1+output_base}:{output_base}\n')
        output_base += output_widths[o]
        if output_widths[o] % 16 != 0:
            output_base += (16 - output_widths[o] % 16)

    tb.write(f'''
module testbench;

    localparam ADDR_WIDTH = $clog2(`NUM_TEST_VECTORS);

    reg [ADDR_WIDTH - 1 : 0] test_vector_addr;

    reg [{input_base}-1: 0] test_vectors [`NUM_TEST_VECTORS - 1 : 0];
    reg [{input_base}-1: 0] test_vector;

    reg [{output_base}-1: 0] test_outputs [`NUM_TEST_VECTORS - 1 : 0];
    reg [{output_base}-1: 0] test_output;

''')
    if sdc_inputs:
        tb.write('    reg [ADDR_WIDTH - 1 : 0] in_addr, pt_addr;  // test_vector_addr as the inputs see it\n')

    has_app_start = hold_reset and "flush" in inputs
    has_window = hold_reset and "stall" in inputs
    if hold_reset:
        tb.write('    integer first_reset;  // first vector with reset asserted (see the initial block)\n')
    if has_app_start:
        tb.write('    integer app_start;    // first flush after it\n')
    if has_window:
        tb.write('    integer app_window;   // first stall release: the power window (cmd.tcl)\n')
    for i in inputs:
        a = addr(i)
        if hold_reset and i == 'reset':
            tb.write(f'    wire {i} = test_vectors[{a}][`SLICE_{i.upper()}] | ({a} < first_reset);\n')
        elif 'reset' not in i:
            tb.write(f'    wire [{input_widths[i]-1}:0] {i} = test_vectors[{a}][`SLICE_{i.upper()}];\n')
        else:
            tb.write(f'    wire {i} = test_vectors[{a}][`SLICE_{i.upper()}];\n')
    for o in outputs:
        tb.write(f'    wire [{output_widths[o]-1}:0] {o};\n')
    if has_window:
        # same address as the stall input: rises in the timestep stall falls
        tb.write(f'    wire saif_window = ({addr("stall")} >= app_window);\n')

    tb.write('''
    reg  clk;
    wire clk_out;
    reg  clk_pass_through;
    wire clk_pass_through_out_bot;
    wire clk_pass_through_out_right;
''')
    if pwr_aware:
        tb.write('''
    supply1 VDD;
    supply0 VSS;
''')

    tb.write(f'''
    {design} dut (
''')

    for i in inputs + outputs:
        tb.write(f'        .{i}({i}),\n')
    if pwr_aware:
        tb.write('''        .VDD(VDD),
        .VSS(VSS),
''')
    if clock_inputs is None and design == 'Tile_PE':
        tb.write('''        .clk_pass_through(clk_pass_through),
        .clk_pass_through_out_bot(clk_pass_through_out_bot),
        .clk_pass_through_out_right(clk_pass_through_out_right),
''')
    elif clock_inputs and "clk_pass_through" in clock_inputs:
        # bundle: clk_pass_through carries the clock in the CGRA too
        tb.write('''        .clk_pass_through(clk),
        .clk_pass_through_out_bot(clk_pass_through_out_bot),
        .clk_pass_through_out_right(clk_pass_through_out_right),
''')

    replay_setup = '''
      first_reset = 0;
      while (first_reset < `NUM_TEST_VECTORS && test_vectors[first_reset][`SLICE_RESET] !== 1'b1)
        first_reset = first_reset + 1;
      if (first_reset == `NUM_TEST_VECTORS)
        first_reset = 0;  // never reset: hold nothing, check every cycle
      $display("replay: reset held and outputs not checked before cycle %0d (first recorded reset)", first_reset);''' \
        if hold_reset else ''
    # run_all_tiles.py does not count X outputs before the app starts (state
    # without reset, which the recording zero-initialized) as mismatches
    if has_app_start:
        replay_setup += '''
      app_start = first_reset;
      while (app_start < `NUM_TEST_VECTORS && test_vectors[app_start][`SLICE_FLUSH] !== 1'b1)
        app_start = app_start + 1;
      if (app_start == `NUM_TEST_VECTORS)
        app_start = first_reset;  // no flush: no pre-app phase
      $display("replay: app starts at cycle %0d (first flush after the reset)", app_start);'''
    if has_window:
        if stall_release is not None:
            fallback, why = str(stall_release), "the other tiles' release"
        else:
            fallback = "app_start" if has_app_start else "first_reset"
            why = "no tile released: the first flush" if has_app_start else "no tile released: the first reset"
        replay_setup += f'''
      app_window = 1;
      while (app_window < `NUM_TEST_VECTORS && !(test_vectors[app_window - 1][`SLICE_STALL] === 1'b1
                                                 && test_vectors[app_window][`SLICE_STALL] === 1'b0))
        app_window = app_window + 1;
      if (app_window == `NUM_TEST_VECTORS)
        app_window = {fallback};  // never stalled ({why})
      $display("replay: power window opens at cycle %0d", app_window);'''
    # hold_reset: no edge until the held reset has reached every flop (an SDF
    # reset tree can take a period; the SRAM's clock is clk & a config flop)
    clock_gen = '''initial begin
      #(`CLK_PERIOD * 4);
      forever #(`CLK_PERIOD/2) clk = ~clk;
    end''' if hold_reset else 'always #(`CLK_PERIOD/2) clk =~clk;'
    init_addrs = '''
      in_addr <= 0;
      pt_addr <= 0;''' if sdc_inputs else ''
    step_addrs = '''
        in_addr <= # `IN_ASSIGNMENT_DELAY (test_vector_addr + 1);
        pt_addr <= # `PT_ASSIGNMENT_DELAY (test_vector_addr + 1);''' if sdc_inputs else ''
    tb.write(f'''        .clk(clk),
        .clk_out(clk_out)
    );

    {clock_gen}

    initial begin
      $readmemh("inputs/test_vectors.txt", test_vectors);
      $readmemh("inputs/test_outputs.txt", test_outputs);{replay_setup}
      clk <= 0;
      test_vector_addr <= 0;{init_addrs}
    end

    always @ (posedge clk) begin
        // Don't change the inputs right after the clock edge because
        // that will cause problems in gate level simulation
        test_vector_addr <= # `ASSIGNMENT_DELAY (test_vector_addr + 1);{step_addrs}
        test_vector <= test_vectors[test_vector_addr];
        test_output <= test_outputs[test_vector_addr];

        if (test_vector_addr >= {num_test_vectors}) begin
            $finish(2);
        end
''')
    for o in outputs:
        differs = f'{o} != test_outputs[test_vector_addr][`SLICE_{o.upper()}] || $isunknown({o})'
        if hold_reset:
            differs = f'test_vector_addr >= first_reset && ({differs})'
        tb.write(f'''
        if ({differs}) begin
            $display("cycle %d: {o}: got %x, expected %x", test_vector_addr, {o}, test_outputs[test_vector_addr][`SLICE_{o.upper()}]);
        end
''')

    tb.write('''
    end

`ifndef NO_SDF
    initial begin
        $sdf_annotate("inputs/design.sdf", testbench.dut,,"testbench_sdf.log","MAXIMUM");
    end
`endif

endmodule''')

    tb.close()


def stall_release(raw_csv):
    """Vector index of the first stall release (a 1 then a 0) in a simvisdbutil
    CSV, or None (no stall column, or never released)."""
    if not os.path.exists(raw_csv):
        return None
    rows = list(csv.reader(open(raw_csv)))
    cols = [i for i, h in enumerate(rows[0] if rows else []) if h.split('.')[-1].split('[')[0] == 'stall']
    if not cols:
        return None

    def bit(v):
        try:
            return int(v, 16)
        except ValueError:
            return None   # x / z
    vals = [bit(r[cols[0]]) for r in rows[1:]]
    for k in range(1, len(vals)):
        if vals[k - 1] == 1 and vals[k] == 0:
            return k
    return None


def pad_vectors(path, n):
    """Repeat the last line of a vector file up to n lines."""
    with open(path) as f:
        lines = f.read().splitlines()
    if lines and len(lines) < n:
        with open(path, 'a') as f:
            f.write((lines[-1] + '\n') * (n - len(lines)))


def main():
    design = os.environ.get('design_name')
    ins, outs, clks = tile_ports(design)
    f = open(f'inputs/tiles_{design}.list', 'r')
    counts, widths, releases = {}, None, {}
    for line in f:
        fields = line.strip().split(',')
        x = fields[-2]
        y = fields[-1]
        tile = f"Tile_X{x}_Y{y}"

        generate_raw(tile, ins, outs)
        releases[tile] = stall_release("raw_input.csv")
        num_test_vectors, input_widths = convert_raw(ins, "raw_input.csv", f"outputs/tile_tbs/{tile}/test_vectors.txt")
        _, output_widths = convert_raw(outs, "raw_output.csv", f"outputs/tile_tbs/{tile}/test_outputs.txt")
        counts[tile] = num_test_vectors
        if widths is None:
            widths = (input_widths, output_widths)
    if not counts:
        return
    # One testbench serves every tile, so it runs the longest tile's vector
    # count. simvisdbutil writes a row per value change while the clock is
    # high, so tiles whose probed signals change mid-cycle get extra rows
    # (an untouched tile can have 2 fewer than a placed one); a shorter tile
    # used to run past the end of its own files -> spurious mismatches. Pad
    # it with its last vector (the tile holds its final state).
    num_test_vectors = max(counts.values())
    for tile, n in counts.items():
        if n < num_test_vectors:
            print(f"@file_info: {tile}: {n} vectors, padded to {num_test_vectors} with its last vector")
            for name in ("test_vectors.txt", "test_outputs.txt"):
                pad_vectors(f"outputs/tile_tbs/{tile}/{name}", num_test_vectors)
    # The window of a tile the app never stalls: where the others are released
    released = [r for r in releases.values() if r is not None]
    common = max(set(released), key=released.count) if released else None
    for tile, r in releases.items():
        if r is None and app_bundle and "stall" in ins:
            print(f"@file_info: {tile}: stall never released (column not stalled by the app); "
                  f"power window from vector {common if common is not None else 'of the first flush'}")
    create_testbench(design, ins, outs, widths[0], widths[1], num_test_vectors, clks,
                     hold_reset=app_bundle, sdc_inputs=app_bundle, stall_release=common)


if __name__ == '__main__':
    main()
