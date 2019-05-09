import magma as m
import fault as f
import shutil
import tempfile
import json
import os
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
        loop = tester.loop(100)
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
            shutil.copy2(self.top_filename,
                         os.path.join(tempdir, "Garnet.v"))
            tester.compile_and_run(target="verilator",
                                   skip_compile=True,
                                   directory=tempdir,
                                   flags=["-Wno-fatal"])


if __name__ == "__main__":
    test = TestBenchGenerator("garnet_stub.v")
