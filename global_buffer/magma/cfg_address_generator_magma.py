import magma
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.generator import Generator
from global_buffer.magma import cfg_address_generator_genesis2

class CfgAddressGenerator(Generator):
    def __init__(self, bank_data_width=64, glb_addr_width=32, config_data_width=32, config_addr_width=32):
        super().__init__()

        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            config_start_pulse=magma.In(magma.Bit),
            config_done_pulse=magma.Out(magma.Bit),

            start_addr=magma.In(magma.Bits[glb_addr_width]),
            num_words=magma.In(magma.Bits[glb_addr_width]),

            cfg_to_cgra_config_wr=magma.Out(magma.Bit),
            cfg_to_cgra_config_addr=magma.Out(magma.Bits[config_addr_width]),
            cfg_to_cgra_config_data=magma.Out(magma.Bits[config_data_width]),

            cfg_to_bank_rd_en=magma.Out(magma.Bits[1]),
            cfg_to_bank_addr=magma.Out(magma.Bits[glb_addr_width])
            bank_to_cfg_rd_data=magma.In(magma.Bits[bank_data_width]),
            bank_to_cfg_rd_data_valid=magma.In(magma.Bits[1]),
        )

        wrapper = cfg_address_generator_genesis2.cfg_addr_gen_wrapper
        generator = wrapper.generator(mode="declare")
        self.underlying = FromMagma(generator())

        self.wire(self.ports.clk, self.underlying.ports.clk)
        self.wire(self.ports.reset, self.underlying.ports.reset)
        self.wire(self.ports.config_start_pulse, self.underlying.ports.config_start_pulse)
        self.wire(self.ports.config_done_pulse, self.underlying.ports.config_done_pulse)

        self.wire(self.ports.start_addr, self.underlying.ports.start_addr)
        self.wire(self.ports.num_words, self.underlying.ports.num_words)

        self.wire(self.ports.cfg_to_cgra_config_wr, self.underlying.ports.cfg_to_cgra_config_wr)
        self.wire(self.ports.cfg_to_cgra_config_addr, self.underlying.ports.cfg_to_cgra_config_addr)
        self.wire(self.ports.cfg_to_cgra_config_data, self.underlying.ports.cfg_to_cgra_config_data)

        self.wire(self.ports.cfg_to_bank_rd_en, self.underlying.ports.cfg_to_bank_rd_en)
        self.wire(self.ports.cfg_to_bank_addr, self.underlying.ports.cfg_to_bank_addr)
        self.wire(self.ports.bank_to_cfg_rd_data, self.underlying.ports.bank_to_cfg_rd_data)
        self.wire(self.ports.bank_to_cfg_rd_data_valid, self.underlying.ports.bank_to_cfg_rd_data_valid)

    # Wire all
    def name(self):
        return f"cfg_address_generator"
