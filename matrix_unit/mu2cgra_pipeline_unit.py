from kratos import Generator, verilog, const, clog2
from global_buffer.design.fifo import FIFO


class mu2cgra_pipeline_unit(Generator):
    def __init__(self, num_output_channels=32, mu_datawidth=16, fifo_depth=2, fifo_name_suffix="mu2cgra_pipeline_fifo", add_flush=False, add_clk_en=True):
        super().__init__(f"mu2cgra_pipeline_unit", debug=True)

        self.mu_datawidth = mu_datawidth
        self.num_output_channels = num_output_channels
        self.fifo_depth = fifo_depth
        self.fifo_name_suffix = fifo_name_suffix

        # Clock and reset
        self.clk = self.clock("clk")
        self.reset = self.reset("reset")

        # Interface with matrix unit
        self.mu2cgra = self.input("mu2cgra", mu_datawidth, size=num_output_channels)
        self.mu2cgra_valid = self.input("mu2cgra_valid", 1)
        self.cgra2mu_ready = self.output("cgra2mu_ready", 1)

        # Interface with CGRA
        self.mu2cgra_d = self.output("mu2cgra_d", mu_datawidth, size=num_output_channels)
        self.mu2cgra_valid_d = self.output("mu2cgra_valid_d", 1)
        self.cgra2mu_ready_d = self.input("cgra2mu_ready_d", 1)

        # Create a FIFO for each channel
        for channel in range(num_output_channels):
            pipeline_fifo = FIFO(self.mu_datawidth, 2)

            fifo_full = self.var(f"fifo_full_{channel}", 1)
            fifo_empty = self.var(f"fifo_empty_{channel}", 1)

            self.add_child(f"pipeline_fifo_channel_{channel}",
                            pipeline_fifo,
                            clk=self.clk,
                            clk_en=const(1, 1),
                            reset=self.reset,
                            # TODO: Figure out what to put here for flush
                            flush=const(0, 1),
                            data_in=self.mu2cgra[channel],
                            data_out=self.mu2cgra_d[channel],
                            push=self.mu2cgra_valid,
                            pop=self.cgra2mu_ready_d,
                            full=fifo_full,
                            empty=fifo_empty,
                            almost_full_diff=1,
                            almost_empty_diff=1)

            if channel == 0:
                self.wire(self.cgra2mu_ready, ~fifo_full)
                self.wire(self.mu2cgra_valid_d, ~fifo_empty)


if __name__ == "__main__":
    dut = mu2cgra_pipeline_unit()
    verilog(dut, filename="mu2cgra_pipeline_unit.sv",
            optimize_if=False)