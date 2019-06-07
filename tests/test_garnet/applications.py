import numpy as np
from commands import *

class OneShotValid():
    def __init__(self, bitstream, infile, goldfile, outfile, args):
        self.bitstream = bitstream
        self.infile = infile
        self.goldfile = goldfile
        self.outfile = outfile
        self.args = args

    def commands(self):
        im = np.fromfile(
            self.infile,
            dtype=np.uint8
        ).astype(np.uint16)

        gold = np.fromfile(
            self.goldfile,
            dtype=np.uint8
        ).astype(np.uint16)

        return [
            WRITE_REG(GLOBAL_RESET_REG, 1),
            # Stall the CGRA
            WRITE_REG(STALL_REG, 0b1111),

            # Configure the CGRA
            PRINT("Configuring CGRA...\n"),
            *gc_config_bitstream(self.bitstream),
            PRINT("Done.\n"),

            # Set up global buffer for pointwise
            *configure_io(IO_INPUT_STREAM, BANK_ADDR(0), len(im), width=self.args.width),
            *configure_io(IO_OUTPUT_STREAM, BANK_ADDR(16), len(gold), width=self.args.width),

            # Put image into global buffer
            WRITE_DATA(BANK_ADDR(0), 0xc0ffee, im.nbytes, im),

            # Start the application
            WRITE_REG(STALL_REG, 0),
            WRITE_REG(CGRA_START_REG, 1),

            WAIT(),
            READ_DATA(
                BANK_ADDR(16),
                gold.nbytes,
                gold,
                _file=self.outfile,
            ),
        ]
