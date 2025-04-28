import kratos
import magma
from kratos import Generator, verilog


class cgra2mu_ready_and(Generator):
    def __init__(self, height=32):
        super().__init__(f"cgra2mu_ready_and_{height}_1", debug=True)

        self.readys_in_packed = self.var("readys_in_packed", height)
        for i in range(height):
            tmp_in = self.input(f"readys_in_{i}", 1)
            self.wire(self.readys_in_packed[i], tmp_in)

        self.anded_ready_out = self.output("anded_ready_out", 1)
        self.wire(self.anded_ready_out, self.readys_in_packed.r_and())

if __name__ == "__main__":
    dut = cgra2mu_ready_and(32)
    verilog(dut, filename="cgra2mu_ready_and.sv",
            optimize_if=False)