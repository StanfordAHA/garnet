import magma as m
import shutil
import json
import os
import sys
from fault import Tester
import glob


def copy_file(src_filename, dst_filename, override=False):
    if not override and os.path.isfile(dst_filename):
        return
    shutil.copy(src_filename, dst_filename)


class BasicTester(Tester):
    def __init__(self, circuit, clock, reset_port=None):
        super().__init__(circuit, clock)
        self.reset_port = reset_port

    def configure(self, addr, data, assert_wr=True):
        self.poke(self.clock, 0)
        self.poke(self.reset_port, 0)
        self.poke(self._circuit.config_config_addr, addr)
        self.poke(self._circuit.config_config_data, data)
        self.poke(self._circuit.config_read, 0)
        # We can use assert_wr switch to check that no reconfiguration
        # occurs when write = 0
        if assert_wr:
            self.poke(self._circuit.config_write, 1)
        else:
            self.poke(self._circuit.config_write, 0)
        #
        self.step(2)
        self.poke(self._circuit.config_write, 0)

    def config_read(self, addr):
        self.poke(self.clock, 0)
        self.poke(self.reset_port, 0)
        self.poke(self._circuit.config_config_addr, addr)
        self.poke(self._circuit.config_read, 1)
        self.poke(self._circuit.config_write, 0)
        self.step(2)

    def reset(self):
        self.poke(self.reset_port, 1)
        self.step(2)
        self.eval()
        self.poke(self.reset_port, 0)


class TestBenchGenerator:
    def __init__(self, top_filename, stub_filename, config_file):
        type_map = {"clk": m.In(m.Clock),
                    "reset": m.In(m.AsyncReset)}

        # detect the environment
        if shutil.which("ncsim"):
            self.use_ncsim = True
        else:
            self.use_ncsim = False
        # if it's ncsim, rename copy it to .sv extension
        if self.use_ncsim:
            new_filename = os.path.splitext(stub_filename)[0] + ".sv"
            shutil.copy2(stub_filename, new_filename)
            stub_filename = new_filename
        self.circuit = m.DefineFromVerilogFile(stub_filename,
                                               target_modules=["Garnet"],
                                               type_map=type_map)[0]

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
        self.output_filename = f"{bitstream_file}.out"
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
        if self.use_ncsim:
            tester.zero_inputs()
        tester.reset()

        # now load the file up
        file_size = os.path.getsize(self.input_filename)
        # file in
        file_in = tester.file_open(self.input_filename, "r")
        file_out = tester.file_open(self.output_filename, "w")
        if len(self.valid_port_name) > 0:
            valid_out = tester.file_open(f"{self.output_filename}.valid", "w")
        else:
            valid_out = None

        # configure it
        for addr, value in self.bitstream:
            tester.configure(addr, value)
            tester.config_read(addr)
            tester.eval()
            tester.expect(self.circuit.read_config_data, value)
        # hit the soft reset button
        if len(self.reset_port_name) > 0:
            # clk = 0
            tester.step(1)
            tester.poke(self.circuit.interface[self.reset_port_name], 1)
            tester.step(2)
            tester.poke(self.circuit.interface[self.reset_port_name], 0)

        loop = tester.loop(file_size)
        value = loop.file_read(file_in)
        loop.poke(self.circuit.interface[self.input_port_name], value)
        loop.eval()
        loop.file_write(file_out, self.circuit.interface[self.output_port_name])
        if valid_out is not None:
            loop.file_write(valid_out,
                            self.circuit.interface[self.valid_port_name])
        loop.step(2)

        tester.file_close(file_in)
        tester.file_close(file_out)
        if valid_out is not None:
            tester.file_close(valid_out)

        # skip the compile and directly to run
        tempdir = "temp/garnet"
        if not os.path.isdir(tempdir):
            os.makedirs(tempdir, exist_ok=True)
        # copy files over
        if self.use_ncsim:
            # coreir always outputs as verilog even though we have system-
            # verilog component
            copy_file(self.top_filename,
                      os.path.join(tempdir, "Garnet.sv"))
        else:
            copy_file(self.top_filename,
                      os.path.join(tempdir, "Garnet.v"))
        cw_files = ["DW_fp_add.v", "DW_fp_mult.v"]
        base_dir = os.path.abspath(os.path.dirname(__file__))
        for filename in cw_files:
            copy_file(os.path.join(base_dir, "peak_core", filename),
                      os.path.join(tempdir, filename))

        # memory core
        copy_file(os.path.join(base_dir,
                               "tests", "test_memory_core",
                               "sram_stub.v"),
                  os.path.join(tempdir, "sram_512w_16b.v"))
        # std cells
        for std_cell in glob.glob(os.path.join(base_dir, "tests/*.sv")):
            copy_file(std_cell,
                      os.path.join(tempdir, os.path.basename(std_cell)))

        for genesis_verilog in glob.glob(os.path.join(base_dir,
                                                      "genesis_verif/*.*")):
            copy_file(genesis_verilog,
                      os.path.join(tempdir, os.path.basename(genesis_verilog)))

        if self.use_ncsim:
            verilogs = list(glob.glob(os.path.join(tempdir, "*.v")))
            verilogs += list(glob.glob(os.path.join(tempdir, "*.sv")))
            verilog_libraries = [os.path.basename(f) for f in verilogs]
            # sanity check since we just copied
            assert "Garnet.sv" in verilog_libraries
            if "Garnet.v" in verilog_libraries:
                # ncsim will freak out if the system verilog file has .v
                # extension
                verilog_libraries.remove("Garnet.v")
                os.remove(os.path.join(tempdir, "Garnet.v"))
            tester.compile_and_run(target="system-verilog",
                                   skip_compile=True,
                                   simulator="ncsim",
                                   # num_cycles is an experimental feature
                                   # need to be merged in fault
                                   num_cycles=1000000,
                                   no_warning=True,
                                   dump_vcd=False,
                                   include_verilog_libraries=verilog_libraries,
                                   directory=tempdir)
        else:
            # fall back to verilator
            # determine whether we should build the verilator target
            verilator_lib = os.path.join(tempdir, "obj_dir", "VGarnet__ALL.a")
            skip_build = os.path.isfile(verilator_lib)
            tester.compile_and_run(target="verilator",
                                   skip_compile=True,
                                   skip_verilator=skip_build,
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
    test.test()
    test.compare()
