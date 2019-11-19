import magma
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.generator import Generator
from global_buffer.magma import memory_bank_genesis2


class MemoryBank(Generator):
    def __init__(self, bank_data_width=64, bank_addr_width=17, config_data_width=32):
        super().__init__()

        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),

            host_wr_en=magma.In(magma.Bit),
            host_wr_addr=magma.In(magma.Bits(bank_addr_width)),
            host_wr_data=magma.In(magma.Bits(bank_data_width)),
            host_wr_data_bit_sel=magma.In(magma.Bits(bank_data_width)),

            host_rd_en=magma.In(magma.Bit),
            host_rd_addr=magma.In(magma.Bits(bank_addr_width)),
            host_rd_data=magma.Out(magma.bits(bank_data_width)),

            cgra_wr_en=magma.In(magma.Bit),
            cgra_wr_addr=magma.In(magma.Bits(bank_addr_width)),
            cgra_wr_data=magma.In(magma.Bits(bank_data_width)),
            cgra_wr_data_bit_sel=magma.In(magma.Bits(bank_data_width)),

            cgra_rd_en=magma.In(magma.Bit),
            cgra_rd_addr=magma.In(magma.Bits(bank_addr_width)),
            cgra_rd_data=magma.Out(magma.Bits(bank_data_width)),

            cfg_rd_en=magma.In(magma.Bit),
            cfg_rd_addr=magma.In(magma.Bits(bank_addr_width)),
            cfg_rd_data=magma.Out(magma.Bits(bank_data_width)),

            config_en=magma.In(magma.Bit),
            config_wr=magma.In(magma.Bit),
            config_rd=magma.In(magma.Bit),
            config_addr=magma.In(magma.Bits(bank_addr_width)),
            config_wr_data=magma.In(magma.Bits(config_data_width)),
            config_rd_data=magma.Out(magma.Bits(config_data_width))
        )

        wrapper = memory_bank_genesis2.memory_bank_wrapper
        generator = wrapper.generator(mode="declare")
        self.underlying = FromMagma(generator())

        self.wire(self.ports.clk, self.underlying.ports.clk)
        self.wire(self.ports.reset, self.underlying.ports.reset)

        self.wire(self.ports.host_wr_en, underlying.ports.host_wr_en)
        self.wire(self.ports.host_wr_addr, underlying.ports.host_wr_addr)
        self.wire(self.ports.host_wr_data, underlying.ports.host_wr_data)
        self.wire(self.ports.host_wr_data_bit_sel, underlying.ports.host_wr_data_bit_sel)

        self.wire(self.ports.host_rd_en, underlying.ports.host_rd_en)
        self.wire(self.ports.host_rd_addr, underlying.ports.host_rd_addr)
        self.wire(self.ports.host_rd_data, underlying.ports.host_rd_data)

        self.wire(self.ports.cgra_wr_en, underlying.ports.cgra_wr_en)
        self.wire(self.ports.cgra_wr_addr, underlying.ports.cgra_wr_addr)
        self.wire(self.ports.cgra_wr_data, underlying.ports.cgra_wr_data)
        self.wire(self.ports.cgra_wr_data_bit_sel, underlying.ports.cgra_wr_data_bit_sel)

        self.wire(self.ports.cgra_rd_en, underlying.ports.cgra_rd_en)
        self.wire(self.ports.cgra_rd_addr, underlying.ports.cgra_rd_addr)
        self.wire(self.ports.cgra_rd_data, underlying.ports.cgra_rd_data)

        self.wire(self.ports.cfg_rd_en, underlying.ports.cfg_rd_en)
        self.wire(self.ports.cfg_rd_addr, underlying.ports.cfg_rd_addr)
        self.wire(self.ports.cfg_rd_data, underlying.ports.cfg_rd_data)

        self.wire(self.ports.config_en, underlying.ports.config_en)
        self.wire(self.ports.config_wr, underlying.ports.config_wr)
        self.wire(self.ports.config_rd, underlying.ports.config_rd)
        self.wire(self.ports.config_addr, underlying.ports.config_addr)
        self.wire(self.ports.config_wr_data, underlying.ports.config_wr_data)
        self.wire(self.ports.config_rd_data, underlying.ports.config_rd_data)


    def name(self):
        return f"memory_bank"
