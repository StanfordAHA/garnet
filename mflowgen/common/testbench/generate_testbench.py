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
if os.path.exists("inputs/manifest.json"):
    manifest = json.load(open("inputs/manifest.json"))  # "{}" without a bundle
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


def create_testbench(design, inputs, outputs, input_widths, output_widths, num_test_vectors, clock_inputs=None):
    pwr_aware = os.environ.get("PWR_AWARE") == "True"

    tb = open("testbench.sv", "w")

    # write defines
    tb.write(f'`timescale 1ns/1ps\n')                           # noqa
    tb.write(f'`define NUM_TEST_VECTORS {num_test_vectors}\n')  # noqa
    tb.write(f'`define ASSIGNMENT_DELAY 0.2 \n')                # noqa
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

    for i in inputs:
        if 'reset' not in i:
            tb.write(f'    wire [{input_widths[i]-1}:0] {i} = test_vectors[test_vector_addr][`SLICE_{i.upper()}];\n')
        else:
            tb.write(f'    wire {i} = test_vectors[test_vector_addr][`SLICE_{i.upper()}];\n')
    for o in outputs:
        tb.write(f'    wire [{output_widths[o]-1}:0] {o};\n')

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

    tb.write(f'''        .clk(clk),
        .clk_out(clk_out)
    );

    always #(`CLK_PERIOD/2) clk =~clk;

    initial begin
      $readmemh("inputs/test_vectors.txt", test_vectors);
      $readmemh("inputs/test_outputs.txt", test_outputs);
      clk <= 0;
      test_vector_addr <= 0;
    end

    always @ (posedge clk) begin
        // Don't change the inputs right after the clock edge because
        // that will cause problems in gate level simulation
        test_vector_addr <= # `ASSIGNMENT_DELAY (test_vector_addr + 1);
        test_vector <= test_vectors[test_vector_addr];
        test_output <= test_outputs[test_vector_addr];

        if (test_vector_addr >= {num_test_vectors}) begin
            $finish(2);
        end
''')
    for o in outputs:
        tb.write(f'''
        if ({o} != test_outputs[test_vector_addr][`SLICE_{o.upper()}] || $isunknown({o})) begin
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


def main():
    design = os.environ.get('design_name')
    ins, outs, clks = tile_ports(design)
    f = open(f'inputs/tiles_{design}.list', 'r')
    i = 0
    for line in f:
        fields = line.strip().split(',')
        x = fields[-2]
        y = fields[-1]
        tile = f"Tile_X{x}_Y{y}"

        generate_raw(tile, ins, outs)
        num_test_vectors, input_widths = convert_raw(ins, "raw_input.csv", f"outputs/tile_tbs/{tile}/test_vectors.txt")
        _, output_widths = convert_raw(outs, "raw_output.csv", f"outputs/tile_tbs/{tile}/test_outputs.txt")
        if i == 0:
            create_testbench(design, ins, outs, input_widths, output_widths, num_test_vectors, clks)
        i += 1


if __name__ == '__main__':
    main()
