import argparse
import magma as m
import shutil
import json
import os
import sys
import filecmp
from fault import Tester
import glob


def copy_file(src_filename, dst_filename, override=False):
    if (
        not override
        and os.path.isfile(dst_filename)
        and filecmp.cmp(src_filename, dst_filename, shallow=False)
    ):
        return
    shutil.copy2(src_filename, dst_filename)


class BasicTester(Tester):
    def __init__(self, circuit, clock, reset_port=None, y_interval=1):
        super().__init__(circuit, clock)
        self.reset_port = reset_port
        self.__xmin = 0xFFFF
        self.__xmax = 0
        self.y_interval = y_interval

        self.__last_addr = None

    def __get_x(self, addr):
        x = (addr >> 8) & 0xFF
        if x > self.__xmax:
            self.__xmax = x
        if x < self.__xmin:
            self.__xmin = x
        return x

    def __clear_last_addr(self, addr):
        if self.__last_addr is not None:
            last_addr = self.__last_addr
            last_x = self.__get_x(last_addr)
            x = self.__get_x(addr)
            if last_x != x:
                self.__last_addr = None
                self.__config_write(last_addr, 0)
                self.__config_read(last_addr, 0)

    def __config_write(self, addr, value):
        self.__clear_last_addr(addr)
        x = self.__get_x(addr)
        port_name = f"config_{x}_write"
        self.poke(self._circuit.interface[port_name], value)
        if value:
            self.__last_addr = addr

    def __config_read(self, addr, value):
        self.__clear_last_addr(addr)
        x = self.__get_x(addr)
        port_name = f"config_{x}_read"
        self.poke(self._circuit.interface[port_name], value)
        if value:
            self.__last_addr = addr

    def __config_addr(self, addr, value):
        x = self.__get_x(addr)
        port_name = f"config_{x}_config_addr"
        self.poke(self._circuit.interface[port_name], value)

    def __config_data(self, addr, value):
        x = self.__get_x(addr)
        port_name = f"config_{x}_config_data"
        self.poke(self._circuit.interface[port_name], value)

    def configure(self, addr, data, assert_wr=True):
        self.poke(self.clock, 0)
        self.poke(self.reset_port, 0)
        self.__config_addr(addr, addr)
        self.__config_data(addr, data)
        self.__config_read(addr, 0)
        # We can use assert_wr switch to check that no reconfiguration
        # occurs when write = 0
        if assert_wr:
            self.__config_write(addr, 1)
        else:
            self.__config_write(addr, 0)
        self.step(2)
        self.__config_write(addr, 0)

    def config_read(self, addr):
        self.poke(self.clock, 0)
        self.poke(self.reset_port, 0)
        self.__config_addr(addr, addr)
        self.__config_read(addr, 1)
        self.__config_write(addr, 0)
        # SRAM content has to be read out immediately
        x = (addr & 0xFF00) >> 8
        if x % 4 == 3:
            self.step(2)
        else:
            self.step(2 * self.y_interval)

    def reset(self):
        self.poke(self.reset_port, 1)
        self.step(2)
        self.eval()
        self.poke(self.reset_port, 0)

    def done_config(self):
        self.poke(self.clock, 0)
        self.poke(self.reset_port, 0)
        # reset all read/write ports touched before
        for x in range(self.__xmin, self.__xmax + 1):
            addr = x << 8
            self.__config_read(addr, 0)
            self.__config_write(addr, 0)
        self.unstall()
        self.step(2)

    def stall(self, max_col):
        mask = 0
        for i in range(max_col):
            mask = (mask << 1) | 1
        self.poke(self._circuit.stall, mask)
        self.eval()
        self.step(2)

    def unstall(self):
        self.poke(self._circuit.stall, 0)
        self.eval()


class TestBenchGenerator:
    def __init__(self, args):
        type_map = {"clk": m.In(m.Clock),
                    "reset": m.In(m.AsyncReset)}

        top_filename = args.top_filename
        stub_filename = args.stub_filename
        config_file = args.config_file

        # detect the environment
        if shutil.which("xrun"):
            self.use_xcelium = True
        else:
            self.use_xcelium = False
        # if it's xcelium, rename copy it to .sv extension
        if self.use_xcelium:
            new_filename = os.path.splitext(stub_filename)[0] + ".sv"
            shutil.copy2(stub_filename, new_filename)
            stub_filename = new_filename
        self.circuit = m.define_from_verilog_file(
            stub_filename,
            target_modules=["Interconnect"],
            type_map=type_map
        )[0]

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
        # compute the config pipeline interval
        max_y = 0
        for addr, _ in self.bitstream:
            y = addr & 0xFF
            if y > max_y:
                max_y = y
        config_pipeline_interval = 8
        self.y_interval = ((max_y - 1) // 8) + 1
        self.input_filename = config["input_filename"]
        self.output_filename = f"{bitstream_file}.out"
        self.gold_filename = config["gold_filename"]
        self.output_port_name = config["output_port_name"]
        self.input_port_name = config["input_port_name"]
        self.valid_port_name = config["valid_port_name"] \
            if "valid_port_name" in config else ""
        self.reset_port_name = config["reset_port_name"] \
            if "reset_port_name" in config else ""
        self.en_port_name = config["en_port_name"]\
            if "en_port_name" in config else ""

        self.top_filename = top_filename

        self._input_size = 1
        self._output_size = 1
        self._loop_size = 0
        self.pixel_size = 1

        self.delay = config["delay"] if "delay" in config else 0

        self._check_input(self.input_filename)
        self._check_output(self.gold_filename)

        # if total cycle set, need to compute delay
        if config.get("total_cycle", 0) > 0:
            total_cycle = config["total_cycle"]
            self.delay += total_cycle - self._loop_size

    def get_max_col(self):
        max_x = 0
        for addr, _ in self.bitstream:
            x = (addr & 0xFFFF) >> 8
            if x > max_x:
                max_x = x
        return max_x + 1

    def _check_input(self, input_filename):
        ext = os.path.splitext(input_filename)[-1]
        assert ext in {".raw", ".pgm"}
        if ext == ".raw":
            self._loop_size = os.path.getsize(self.input_filename)
            return
        else:
            output_filename = input_filename + ".raw"
            self._input_size, self._loop_size = \
                self._convert_pgm_to_raw(input_filename, output_filename)
            self.input_filename = output_filename

    def _check_output(self, input_filename):
        ext = os.path.splitext(input_filename)[-1]
        print(ext)
        assert ext in {".raw", ".pgm"}
        if ext == ".raw":
            return
        else:
            output_filename = input_filename + ".raw"
            self._output_size, _ = self._convert_pgm_to_raw(input_filename,
                                                            output_filename)
            self.gold_filename = output_filename

    def _convert_pgm_to_raw(self, input_filename, output_filename):
        from functools import reduce
        eight_bit = (1 << 8) - 1
        sixteen_bit = (1 << 16) - 1
        # convert the pgm into raws and keep track of the input size as well as
        # the input image size
        with open(input_filename, "rb") as f:
            pgm_format = f.readline().decode("ascii").strip()
            assert pgm_format in {"P5", "P6"}
            shape = [int(i) for i in f.readline().decode("ascii").split()]
            wxh = reduce(lambda x, y: x * y, shape)
            depth = int(f.readline().decode("ascii"))
            assert depth in [eight_bit, sixteen_bit]
            input_size = 1 if depth == eight_bit else 2
            self.pixel_size = 1 if pgm_format == "P5" else 3
            loop_size = wxh * self.pixel_size
            # convert it to a raw file
            with open(output_filename, "wb+") as out_f:
                for i in range(loop_size):
                    if input_size == 1:
                        out_f.write(f.read(1))
                    else:
                        i0 = f.read(1)
                        i1 = f.read(1)
                        # change from bit-endian to little-endian
                        out_f.write(i1)
                        out_f.write(i0)
        return input_size, loop_size

    def test(self):
        tester = BasicTester(self.circuit, self.circuit.clk, self.circuit.reset,
                             y_interval=self.y_interval)
        if self.use_xcelium:
            tester.zero_inputs()
        tester.reset()

        # now load the file up

        # file in
        file_in = tester.file_open(self.input_filename, "r",
                                   chunk_size=self._input_size)
        file_out = tester.file_open(self.output_filename, "w",
                                    chunk_size=self._output_size)
        if len(self.valid_port_name) > 0:
            valid_out = tester.file_open(f"{self.output_filename}.valid", "w")
        else:
            valid_out = None

        # before configuration stall it
        tester.stall(self.get_max_col())

        # configure it
        for addr, value in self.bitstream:
            tester.configure(addr, value)
            tester.eval()

        for addr, value in self.bitstream:
            tester.config_read(addr)
            tester.eval()
            tester.expect(self.circuit.read_config_data, value)

        tester.done_config()

        # hit the soft reset button
        if len(self.reset_port_name) > 0:
            # clk = 0
            tester.step(1)
            tester.poke(self.circuit.interface[self.reset_port_name], 1)
            tester.step(2)
            tester.poke(self.circuit.interface[self.reset_port_name], 0)

        # enable port
        if len(self.en_port_name) > 0:
            for port in self.en_port_name:
                tester.poke(self.circuit.interface[port], 1)

        input_port_names = self.input_port_name[:]
        input_port_names.sort()
        output_port_names = self.output_port_name[:]
        output_port_names.sort()

        loop = tester.loop(self._loop_size * len(input_port_names))
        for input_port_name in input_port_names:
            value = loop.file_read(file_in)
            loop.poke(self.circuit.interface[input_port_name], value)
            loop.eval()
        for output_port_name in output_port_names:
            loop.file_write(file_out, self.circuit.interface[output_port_name])
        if valid_out is not None:
            loop.file_write(valid_out,
                            self.circuit.interface[self.valid_port_name])
        loop.step(2)

        # delay loop
        if self.delay > 0:
            delay_loop = tester.loop(self.delay)
            for input_port_name in input_port_names:
                delay_loop.poke(self.circuit.interface[input_port_name], 0)
                delay_loop.eval()
            for output_port_name in output_port_names:
                delay_loop.file_write(file_out, self.circuit.interface[output_port_name])
            if valid_out is not None:
                delay_loop.file_write(valid_out,
                                      self.circuit.interface[self.valid_port_name])
            delay_loop.step(2)

        tester.file_close(file_in)
        tester.file_close(file_out)
        if valid_out is not None:
            tester.file_close(valid_out)

        # skip the compile and directly to run
        tempdir = "temp/garnet"
        if not os.path.isdir(tempdir):
            os.makedirs(tempdir, exist_ok=True)
        # copy files over
        if self.use_xcelium:
            # coreir always outputs as verilog even though we have system-
            # verilog component
            copy_file(self.top_filename,
                      os.path.join(tempdir, "Interconnect.sv"))
        else:
            copy_file(self.top_filename,
                      os.path.join(tempdir, "Interconnect.v"))
        # dw_files = ["DW_fp_add.v", "DW_fp_mult.v", "DW_fp_addsub.v"]
        cw_files = ["CW_fp_add.v", "CW_fp_mult.v"]
        base_dir = os.path.abspath(os.path.dirname(__file__))
        # cad_dir = "/cad/synopsys/dc_shell/J-2014.09-SP3/dw/sim_ver/"
        cad_dir = "/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/"
        for filename in cw_files:
            if os.path.isdir(cad_dir):
                print("Use CW IP for", filename)
                copy_file(os.path.join(cad_dir, filename),
                          os.path.join(tempdir, filename))
            else:
                if filename == "DW_fp_addsub.v":
                    # travis doesn't need it
                    continue
                copy_file(os.path.join(base_dir, "peak_core", filename),
                          os.path.join(tempdir, filename))

        # std cells
        for std_cell in glob.glob(os.path.join(base_dir, "tests/*.sv")):
            copy_file(std_cell,
                      os.path.join(tempdir, os.path.basename(std_cell)))

        for genesis_verilog in glob.glob(os.path.join(base_dir,
                                                      "genesis_verif/*.*")):
            copy_file(genesis_verilog,
                      os.path.join(tempdir, os.path.basename(genesis_verilog)))

        if self.use_xcelium:
            verilogs = list(glob.glob(os.path.join(tempdir, "*.v")))
            verilogs += list(glob.glob(os.path.join(tempdir, "*.sv")))
            verilog_libraries = [os.path.basename(f) for f in verilogs]
            # sanity check since we just copied
            assert "Interconnect.sv" in verilog_libraries
            for name in ["Interconnect.v", "Interconnect.sv"]:
                if name in verilog_libraries:
                    # ncsim will freak out if the system verilog file has .v or .sv
                    # extension
                    verilog_libraries.remove(name)
                    # os.remove(os.path.join(tempdir, name))
            tester.compile_and_run(target="system-verilog",
                                   skip_compile=True,
                                   skip_run=args.tb_only,
                                   simulator="xcelium",
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
                        if pos % (self.pixel_size * self._input_size) == 0:
                            onebit_byte = onebit_f.read(1)
                        if not design_byte:
                            break
                        pos += 1
                        design_byte = ord(design_byte)
                        if not isinstance(onebit_byte, int):
                            onebit_byte = ord(onebit_byte)
                        onebit_byte = onebit_byte if has_valid else 1
                        if onebit_byte != 1:
                            skipped_pos += 1
                            continue
                        halide_byte = halide_f.read(1)
                        if len(halide_byte) == 0:
                            break
                        halide_byte = ord(halide_byte)
    #                    print("pos:", pos, "design:", design_byte, "halide:", halide_byte)
                        if design_byte != halide_byte:
                            print("pos:", pos, "design:", design_byte, "halide:", halide_byte)
                       #     print("design:", design_byte, file=sys.stderr)
                       #     print("halide:", halide_byte, file=sys.stderr)
    #                        raise Exception("Error at pos " + str(pos), "real pos",
    #                                       pos - skipped_pos)

        compared_size = pos - skipped_pos
        assert compared_size > 0, "Got 0 valid outputs"

        if compared_size != compare_size:
            print("Expected to produce " + str(compare_size) +
                            " valid bytes, got " + str(compared_size))
        print("PASS: compared with", pos - skipped_pos, "bytes")
        print("Skipped", skipped_pos, "bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("top_filename")
    parser.add_argument("stub_filename")
    parser.add_argument("config_file")
    parser.add_argument("--tb-only", action="store_true")
    args = parser.parse_args()

    test = TestBenchGenerator(args)
    test.test()
    test.compare()
