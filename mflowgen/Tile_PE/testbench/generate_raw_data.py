# Generates raw_input.csv and raw_output.csv from waveform produced by xrun
# Run when you want to update those files with outputs from a new testbench

from defines import inputs, outputs, scope

def main():
    sv = open('waveform_to_csv.sh', 'w')

    tile = "Tile_X09_Y08"
    waveform = "conv_3_3.trn"

    input_signals = ' '.join([f'-signal {scope}.{tile}.{i}' for i in inputs])
    output_signals = ' '.join([f'-signal {scope}.{tile}.{o}' for o in outputs])
    flags = [
        "-overwrite",
        "-xsub 0",
        "-timeunits ps",
        "-radix hex",
        "-notime",
    ]
    flag_string = ' '.join(flags)

    sv.write(f'simvisdbutil {waveform} {input_signals} -output raw_input.csv {flag_string}\n')
    sv.write(f'simvisdbutil {waveform} {output_signals} -output raw_output.csv {flag_string}\n')

    sv.close()

if __name__ == '__main__':
    main()
