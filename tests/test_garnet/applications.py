import numpy as np

class OneShotValid():
    def __init__(self, bitstream, infile, goldfile, outfile):
        self.bitstream = bitstream
        self.infile = infile
        self.goldfile = goldfile
        self.outfile = outfile

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
            *gc_config_bitstream(self.bitstream),

            # Set up global buffer for pointwise
            *configure_io(IO_INPUT_STREAM, BANK_ADDR(0), len(im), width=args.width),
            *configure_io(IO_OUTPUT_STREAM, BANK_ADDR(16), len(gold), width=args.width),

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
                _file=tester.file_open(self.outfile, "wb", 8),
            ),
        ]
