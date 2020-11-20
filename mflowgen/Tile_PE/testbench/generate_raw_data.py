# Generates raw_input.csv and raw_output.csv from waveform produced by xrun
# Run when you want to update those files with outputs from a new testbench

from defines import inputs, outputs, scope
import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--waveform', default='waveforms', type=str)
    parser.add_argument('--tile', default='Tile_X09_Y08', type=str)
    args = parser.parse_args()

    sv = open('waveform_to_csv.sh', 'w')

    tile = args.tile
    waveform = args.waveform
    clock_period = float(os.environ.get("clock_period"))

    input_signals = ' '.join([f'-signal {scope}.{tile}.{i}' for i in inputs])
    output_signals = ' '.join([f'-signal {scope}.{tile}.{o}' for o in outputs])
    flags = [
        "-overwrite",
        "-xsub 0",
        "-timeunits ps",
        "-radix hex",
        "-64bit",
        f"-period {int(clock_period*1000)}ps",
        "-notime",
    ]
    flag_string = ' '.join(flags)

    sv.write(f'if [ ! -f {waveform}.trn ]; then\nsimvisdbutil {waveform}.vcd -sst2\nfi\n')
    sv.write(f'simvisdbutil {waveform}.trn {input_signals} -output raw_input.csv {flag_string}\n')
    sv.write(f'simvisdbutil {waveform}.trn {output_signals} -output raw_output.csv {flag_string}\n')

    sv.close()

if __name__ == '__main__':
    main()
