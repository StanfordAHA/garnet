import magma as m
import shutil
import tempfile
import json
import os
import sys
from gemstone.common.testers import BasicTester


class TestBenchGenerator:
    def __init__(self, top_filename, stub_filename, config_file):
        type_map = {"clk": m.In(m.Clock),
                    "reset": m.In(m.AsyncReset)}
        self.circuit = m.DefineFromVerilogFile(stub_filename,
                                               target_modules=["Garnet"],
                                               type_map=type_map)

        with open(config_file) as f:
            config = json.load(f)

        bitstream_file = config["bitstream"]

        # load the bitstream
        self.bitstream = []
        with open(bitstream_file) as f:
            for line in f.readlines():
                addr, value = line.strip().split(" ")
                addr = int(addr, 16)
                value = int(value, 16)
                self.bitstream.append((addr, value))
        self.input_filename = config["input_filename"]
        self.output_filename = config["output_filename"]
        self.gold_filename = config["gold_filename"]
        self.output_port_name = config["output_port_name"]
        self.input_port_name = config["input_port_name"]
        self.valid_port_name = config["valid_port_name"] \
            if "valid_port_name" in config else ""
        self.reset_port_name = config["reset_port_name"] \
            if "reset_port_name" in config else ""

        self.top_filename = top_filename

    def test(self):
        tester = BasicTester(self.circuit, self.circuit.clk, self.circuit.reset)
        tester.reset()

        # configure it
        for addr, value in self.bitstream:
            tester.configure(addr, value)
            tester.config_read(addr)
            tester.eval()
            tester.expect(self.circuit.read_config_data, value)
        # hit the soft reset button
        if len(self.reset_port_name) > 0:
            tester.poke(self.circuit.interface[self.reset_port_name], 1)
            tester.step(2)
            tester.eval()
            tester.poke(self.circuit.interface[self.reset_port_name], 0)
            tester.eval()

        # now load the file up
        file_size = os.path.getsize(self.input_filename)
        loop = tester.loop(file_size)
        # file in
        file_in = tester.file_open(self.input_filename, "r")
        file_out = tester.file_open(self.output_filename, "w")
        if len(self.valid_port_name) > 0:
            valid_out = tester.file_open(f"{self.output_filename}.valid", "w")
        else:
            valid_out = None

        value = loop.file_read(file_in)
        loop.poke(self.circuit.interface[self.input_port_name], value)
        loop.eval()
        loop.step(2)
        loop.eval()
        loop.file_write(file_out, self.circuit.interface[self.output_port_name])
        if valid_out is not None:
            loop.file_write(valid_out,
                            self.circuit.interface[self.valid_port_name])

        tester.file_close(file_in)
        tester.file_close(file_out)
        if valid_out is not None:
            tester.file_close(valid_out)

        # skip the compile and directly to run
        with tempfile.TemporaryDirectory() as tempdir:
            # copy files over
            shutil.copy2(self.top_filename,
                         os.path.join(tempdir, "Garnet.v"))
            cw_files = ["CW_fp_add.v", "CW_fp_mult.v"]
            base_dir = os.path.abspath(os.path.dirname(__file__))
            for filename in cw_files:
                shutil.copy(os.path.join(base_dir, "peak_core", filename),
                            tempdir)
            shutil.copy(os.path.join(base_dir,
                                     "tests", "test_memory_core",
                                     "sram_stub.v"),
                        os.path.join(tempdir, "sram_512w_16b.v"))
            tester.compile_and_run(target="verilator",
                                   skip_compile=True,
                                   directory=tempdir,
                                   flags=["-Wno-fatal"])

    def compare(self):
        assert os.path.isfile(self.output_filename)
        if len(self.valid_port_name) == 0:
            valid_filename = "/dev/null"
            has_valid = False
        else:
            valid_filename = f"{self.output_filename}.valid"
            has_valid = True

        # the code before is taken from the code I wrote for CGRAFlow
        compare_size = os.path.getsize(self.gold_filename)
        with open(self.output_filename, "rb") as design_f:
            with open(self.gold_filename, "rb") as halide_f:
                with open(valid_filename, "rb") as onebit_f:
                    pos = 0
                    skipped_pos = 0
                    while True:
                        design_byte = design_f.read(1)
                        onebit_byte = onebit_f.read(1)
                        if not design_byte:
                            break
                        pos += 1
                        design_byte = ord(design_byte)
                        onebit_byte = ord(onebit_byte) if has_valid else 1
                        if onebit_byte != 1:
                            skipped_pos += 1
                            continue
                        halide_byte = ord(halide_f.read(1))
                        if design_byte != halide_byte:
                            print("design:", design_byte, file=sys.stderr)
                            print("halide:", halide_byte, file=sys.stderr)
                            raise Exception("Error at pos " + str(pos))

        compared_size = pos - skipped_pos
        if compared_size != compare_size:
            raise Exception("Expected to produce " + str(compare_size) +
                            " valid bytes, got " + str(compared_size))
        print("PASS: compared with", pos - skipped_pos, "bytes")
        print("Skipped", skipped_pos, "bytes")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python", sys.argv[0], "top_filename", "stub_filename",
              "config.json", file=sys.stderr)
        exit(1)
    test = TestBenchGenerator(sys.argv[1], sys.argv[2], sys.argv[3])
