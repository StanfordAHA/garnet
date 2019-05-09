import magma as m
import fault as f
from gemstone.common.testers import BasicTester


class TestBenchGenerator:
    def __init__(self, top_filename, bitstream_file, input_filename,
                 output_filename,
                 valid_port_name="",
                 reset_port_name=""):
        type_map = {"clk": m.In(m.Clock),
                    "reset": m.In(m.AsyncReset)}
        self.circuit = m.DefineFromVerilogFile(top_filename,
                                               target_modules=["Garnet"],
                                               type_map=type_map)

        # load the bitstream
        self.bitstream = []
        with open(bitstream_file) as f:
            for line in f.readlines():
                addr, value = line.strip().split(" ")
                addr = int(addr, 16)
                value = int(value, 16)
                self.bitstream.append((addr, value))
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.valid_port_name = valid_port_name
        self.reset_port_name = reset_port_name

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

        tester.file_close(file_in)
        tester.file_close(file_out)
        if valid_out is not None:
            tester.file_close(valid_out)


if __name__ == "__main__":
    test = TestBenchGenerator("garnet_stub.v")
