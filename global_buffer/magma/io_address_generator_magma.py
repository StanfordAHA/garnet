import magma
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.generator import Generator
from . import io_address_generator_genesis2


class IoAddressGenerator(Generator):
    def __init__(self, bank_data_width=64, cgra_data_width=16, glb_addr_width=32, config_data_width=32, idle_mode=0):
        super().__init__()

        self.add_ports(
            clk=magma.In(magma.Clock),
            clk_en=magma.In(magma.Bit),
            reset=magma.In(magma.AsyncReset),
            cgra_start_pulse=magma.In(magma.Bit),
            cgra_done_pulse=magma.Out(magma.Bit),

            start_addr=magma.In(magma.Bits[glb_addr_width]),
            num_words=magma.In(magma.Bits[glb_addr_width]),
            mode=magma.In(magma.Bits[2]),
            done_delay=magma.In(magma.Bits[config_data_width]),

            cgra_to_io_wr_en=magma.In(magma.Bit),
            cgra_to_io_rd_en=magma.In(magma.Bit),
            cgra_to_io_wr_data=magma.In(magma.Bits[cgra_data_width]),
            io_to_cgra_rd_data=magma.Out(magma.Bits[cgra_data_width]),
            io_to_cgra_rd_data_valid=magma.Out(magma.Bit),
            cgra_to_io_addr_high=magma.In(magma.Bits[cgra_data_width]),
            cgra_to_io_addr_low=magma.In(magma.Bits[cgra_data_width]),

            io_to_bank_wr_en=magma.Out(magma.Bits[1]),
            io_to_bank_wr_data=magma.Out(magma.Bits[bank_data_width]),
            io_to_bank_wr_data_bit_sel=magma.Out(magma.Bits[bank_data_width]),
            io_to_bank_rd_en=magma.Out(magma.Bits[1]),
            bank_to_io_rd_data=magma.In(magma.Bits[bank_data_width]),
            bank_to_io_rd_data_valid=magma.In(magma.Bits[1]),
            io_to_bank_addr=magma.Out(magma.Bits[glb_addr_width])
        )

        wrapper = io_address_generator_genesis2.io_addr_gen_wrapper
        generator = wrapper.generator(mode="declare")
        self.underlying = FromMagma(generator())

        self.wire(self.ports.clk, self.underlying.ports.clk)
        self.wire(self.ports.clk_en, self.underlying.ports.clk_en)
        self.wire(self.ports.reset, self.underlying.ports.reset)
        self.wire(self.ports.cgra_start_pulse, self.underlying.ports.cgra_start_pulse)
        self.wire(self.ports.cgra_done_pulse, self.underlying.ports.cgra_done_pulse)

        self.wire(self.ports.start_addr, self.underlying.ports.start_addr)
        self.wire(self.ports.num_words, self.underlying.ports.num_words)
        self.wire(self.ports.mode, self.underlying.ports.mode)
        self.wire(self.ports.done_delay, self.underlying.ports.done_delay)

        self.wire(self.ports.cgra_to_io_wr_en, self.underlying.ports.cgra_to_io_wr_en)
        self.wire(self.ports.cgra_to_io_rd_en, self.underlying.ports.cgra_to_io_rd_en)
        self.wire(self.ports.cgra_to_io_wr_data, self.underlying.ports.cgra_to_io_wr_data)
        self.wire(self.ports.io_to_cgra_rd_data, self.underlying.ports.io_to_cgra_rd_data)
        self.wire(self.ports.io_to_cgra_rd_data_valid, self.underlying.ports.io_to_cgra_rd_data_valid)
        self.wire(self.ports.cgra_to_io_addr_high, self.underlying.ports.cgra_to_io_addr_high)
        self.wire(self.ports.cgra_to_io_addr_low, self.underlying.ports.cgra_to_io_addr_low)

        self.wire(self.ports.io_to_bank_wr_en[0], self.underlying.ports.io_to_bank_wr_en)
        self.wire(self.ports.io_to_bank_wr_data, self.underlying.ports.io_to_bank_wr_data)
        self.wire(self.ports.io_to_bank_wr_data_bit_sel, self.underlying.ports.io_to_bank_wr_data_bit_sel)
        self.wire(self.ports.io_to_bank_rd_en[0], self.underlying.ports.io_to_bank_rd_en)
        self.wire(self.ports.bank_to_io_rd_data, self.underlying.ports.bank_to_io_rd_data)
        self.wire(self.ports.bank_to_io_rd_data_valid[0], self.underlying.ports.bank_to_io_rd_data_valid)
        self.wire(self.ports.io_to_bank_addr, self.underlying.ports.io_to_bank_addr)

    # Wire all
    def name(self):
        return f"io_address_generator"
