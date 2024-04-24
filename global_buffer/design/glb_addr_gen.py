import os
from kratos import always_ff, posedge, Generator, clog2
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class GlbAddrGen(Generator):
    ''' Generate addresses '''

    def __init__(self, _params: GlobalBufferParams, loop_level: int):
        if os.getenv('WHICH_SOC') == "amber":
            super().__init__("glb_addr_gen")
        else:
            super().__init__(f"glb_addr_gen_{loop_level}")
        self._params = _params
        self.p_addr_width = self.param("addr_width", width=32, value=32)
        if os.getenv('WHICH_SOC') == "amber":
            self.p_loop_level = self._params.loop_level
            self.loop_level = self._params.loop_level
        else:
            self.p_loop_level = self.param("loop_level", width=32, value=self._params.loop_level)
            self.loop_level = loop_level

        self.clk = self.clock("clk")
        self.clk_en = self.clock_en("clk_en")
        self.reset = self.reset("reset")
        self.restart = self.input("restart", 1)
        self.strides = self.input("strides", self.p_addr_width,
                                  size=self.p_loop_level,
                                  packed=True, explicit_array=True)
        self.start_addr = self.input("start_addr", self.p_addr_width)
        self.step = self.input("step", 1)
        self.mux_sel = self.input("mux_sel", max(clog2(self.loop_level), 1))
        self.addr_out = self.output("addr_out", self.p_addr_width)

        # local variables
        self.current_addr = self.var("current_addr", self.p_addr_width)

        # output address
        self.wire(self.addr_out, self.start_addr + self.current_addr)
        self.add_always(self.calculate_address)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def calculate_address(self):
        if self.reset:
            self.current_addr = 0
        elif self.clk_en:
            if self.restart:
                self.current_addr = 0
            elif self.step:
                self.current_addr = self.current_addr + self.strides[self.mux_sel]
