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

            # Enable interrupts
            WRITE_REG(INTERRUPT_ENABLE_REG, 0b11),

            # WRITE_REG(CGRA_SOFT_RESET_EN_REG, 1),  # TODO: removeme
            # WRITE_REG(SOFT_RESET_DELAY_REG, 0),  # TODO: removeme

            # Configure the CGRA
            PRINT("Configuring CGRA..."),
            # *gc_config_bitstream(self.bitstream),
            *gb_config_bitstream(self.bitstream, width=self.args.width),
            PRINT("Done."),

            # # TODO: Do it again to test the interrupts, but remove later.
            # PRINT("Configuring CGRA..."),
            # # *gc_config_bitstream(self.bitstream),
            # *gb_config_bitstream(self.bitstream, width=self.args.width),
            # PRINT("Done."),

            # Set up global buffer for pointwise
            *configure_io(IO_INPUT_STREAM, BANK_ADDR(0), len(im), width=self.args.width),
            # TODO: would be better if this took in the input and
            # output tiles of the application and then configured the
            # io controllers appropriately.
            *configure_io(IO_OUTPUT_STREAM, BANK_ADDR(16), len(gold), io_ctrl=1, width=self.args.width),
            # *configure_io(IO_OUTPUT_STREAM, BANK_ADDR(16), len(gold), width=self.args.width),
            # *configure_io(IO_OUTPUT_STREAM, BANK_ADDR(4), len(gold), width=self.args.width),

            # Put image into global buffer
            PRINT("Transferring input data..."),
            WRITE_DATA(BANK_ADDR(0), 0xc0ffee, im.nbytes, im),
            PRINT("Done."),

            # Start the application
            PRINT("Starting application..."),
            WRITE_REG(STALL_REG, 0),
            PEND(0b01, "start"),
            WRITE_REG(CGRA_START_REG, 1),
            PRINT("Waiting for completion..."),
            WAIT(0b01, "start"),
            PRINT("Done."),

            PRINT("Reading output data..."),
            READ_DATA(
                BANK_ADDR(16),
                gold.nbytes,
                gold,
                _file=self.outfile,
            ),
            PRINT("All tasks complete!"),
        ]

    def verify(self, result=None):
        print("Comparing outputs...")
        gold = np.fromfile(
            self.goldfile,
            dtype=np.uint8,
        )

        if result is None:
            result = np.fromfile(
                self.outfile,
                dtype=np.uint16,
            ).astype(np.uint8)

        if not np.array_equal(gold, result):
            if len(gold) != len(result):
                print(f"ERROR: Expected {len(gold)} outputs but got {len(result)}")
            for k, (x, y) in enumerate(zip(gold, result)):
                if x != y:
                    print(f"ERROR: [{k}] expected 0x{x:x} but got 0x{y:x}")
            return False

        print("Outputs match!")
        return True

class OneShotStall(OneShotValid):
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

            # Enable interrupts
            WRITE_REG(INTERRUPT_ENABLE_REG, 0b11),

            # WRITE_REG(CGRA_SOFT_RESET_EN_REG, 1),  # TODO: removeme
            # WRITE_REG(SOFT_RESET_DELAY_REG, 0),  # TODO: removeme

            # Configure the CGRA
            PRINT("Configuring CGRA..."),
            # *gc_config_bitstream(self.bitstream),
            *gb_config_bitstream(self.bitstream, width=self.args.width),
            PRINT("Done."),

            # # TODO: Do it again to test the interrupts, but remove later.
            # PRINT("Configuring CGRA..."),
            # # *gc_config_bitstream(self.bitstream),
            # *gb_config_bitstream(self.bitstream, width=self.args.width),
            # PRINT("Done."),

            # Set up global buffer for pointwise
            *configure_io(IO_INPUT_STREAM, BANK_ADDR(0), len(im), width=self.args.width),
            # TODO: would be better if this took in the input and
            # output tiles of the application and then configured the
            # io controllers appropriately.
            *configure_io(IO_OUTPUT_STREAM, BANK_ADDR(16), len(gold), io_ctrl=1, width=self.args.width),
            # *configure_io(IO_OUTPUT_STREAM, BANK_ADDR(16), len(gold), width=self.args.width),
            # *configure_io(IO_OUTPUT_STREAM, BANK_ADDR(4), len(gold), width=self.args.width),

            # Put image into global buffer
            PRINT("Transferring input data..."),
            WRITE_DATA(BANK_ADDR(0), 0xc0ffee, im.nbytes, im),
            PRINT("Done."),

            # Start the application
            PRINT("Starting application..."),
            WRITE_REG(STALL_REG, 0),
            PEND(0b01, "start"),
            WRITE_REG(CGRA_START_REG, 1),

            WRITE_REG(STALL_REG, 0b1111),  # HACK
            STALL(50),  # HACK
            WRITE_REG(STALL_REG, 0),  # HACK

            STALL(100),  # HACK

            WRITE_REG(STALL_REG, 0b1111),  # HACK
            STALL(50),  # HACK
            WRITE_REG(STALL_REG, 0),  # HACK

            STALL(100),  # HACK

            WRITE_REG(STALL_REG, 0b1111),  # HACK
            STALL(50),  # HACK
            WRITE_REG(STALL_REG, 0),  # HACK

            PRINT("Waiting for completion..."),
            WAIT(0b01, "start"),
            PRINT("Done."),

            PRINT("Reading output data..."),
            READ_DATA(
                BANK_ADDR(16),
                gold.nbytes,
                gold,
                _file=self.outfile,
            ),
            PRINT("All tasks complete!"),
        ]
