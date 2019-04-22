import magma
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.const import Const
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.generator import Generator
from . import global_buffer_genesis2
import math


class GlobalBuffer(Generator):
    def __init__(self, num_banks, bank_addr_width, bank_data_width,\
            num_io, num_cfg, cgra_data_width, top_cfg_addr,\
            cfg_addr, cfg_data):
        super().__init__()

        self.num_banks = num_banks
        self.bank_data_width = bank_data_width
        self.bank_addr_width = bank_addr_width
        self.glb_addr_width = math.ceil(math.log2(self.num_banks))\
                + self.bank_addr_width
        self.num_io = num_io
        self.num_cfg = num_cfg
        self.cgra_data_width = cgra_data_width
        self.cfg_addr = cfg_addr
        self.top_cfg_addr = top_cfg_addr
        self.cfg_data = cfg_data

        self.top_config_type = ConfigurationType(\
                self.top_cfg_addr, self.cfg_data)
        self.glb_config_type = ConfigurationType(\
                self.cfg_addr, self.cfg_data)

        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),

            host_wr_en=magma.In(magma.Bits[1]),
            host_wr_addr=magma.In(magma.Bits[self.glb_addr_width]),
            host_wr_data=magma.In(magma.Bits[self.bank_data_width]),

            host_rd_en=magma.In(magma.Bits[1]),
            host_rd_addr=magma.In(magma.Bits[self.glb_addr_width]),
            host_rd_data=magma.Out(magma.Bits[self.bank_data_width]),

            cgra_to_io_stall=magma.In(magma.Bits[self.num_io*1]),
            cgra_to_io_wr_en=magma.In(magma.Bits[self.num_io*1]),
            cgra_to_io_rd_en=magma.In(magma.Bits[self.num_io*1]),
            io_to_cgra_rd_data_valid=magma.Out(magma.Bits[self.num_io*1]),
            cgra_to_io_wr_data=magma.In(\
                    magma.Bits[self.num_io*self.cgra_data_width]),
            io_to_cgra_rd_data=magma.Out(\
                    magma.Bits[self.num_io*self.cgra_data_width]),
            cgra_to_io_addr_high=magma.In(\
                    magma.Bits[self.num_io*self.cgra_data_width]),
            cgra_to_io_addr_low=magma.In(\
                    magma.Bits[self.num_io*self.cgra_data_width]),

            glb_to_cgra_cfg_wr=magma.Out(\
                    magma.Bits[self.num_cfg*1]),
            glb_to_cgra_cfg_addr=magma.Out(\
                    magma.Bits[self.num_cfg*self.cfg_addr]),
            glb_to_cgra_cfg_data=magma.Out(\
                    magma.Bits[self.num_cfg*self.cfg_data]),

            glc_to_io_stall=magma.In(magma.Bits[1]),
            glc_to_cgra_cfg_wr=magma.In(magma.Bits[1]),
            glc_to_cgra_cfg_addr=magma.In(magma.Bits[cfg_addr]),
            glc_to_cgra_cfg_data=magma.In(magma.Bits[cfg_data]),

            cgra_start_pulse=magma.In(magma.Bits[1]),
            config_start_pulse=magma.In(magma.Bits[1]),
            config_done_pulse=magma.Out(magma.Bits[1]),

            glb_config=magma.In(self.glb_config_type),
            glb_config_rd_data=magma.Out(magma.Bits[cfg_data]),

            top_config=magma.In(self.top_config_type),
            top_config_rd_data=magma.Out(magma.Bits[cfg_data])
        )

        wrapper = global_buffer_genesis2.glb_wrapper
        generator = wrapper.generator(mode="declare")
        self.underlying = FromMagma(generator())

        self.wire(self.ports.clk, self.underlying.ports.clk)
        self.wire(self.ports.reset, self.underlying.ports.reset)

        self.wire(self.ports.host_wr_en,\
                self.underlying.ports.host_wr_en)
        self.wire(self.ports.host_wr_addr,\
                self.underlying.ports.host_wr_addr)
        self.wire(self.ports.host_wr_data,\
                self.underlying.ports.host_wr_data)

        self.wire(self.ports.host_rd_en,\
                self.underlying.ports.host_rd_en)
        self.wire(self.ports.host_rd_addr,\
                self.underlying.ports.host_rd_addr)
        self.wire(self.ports.host_rd_data,\
                self.underlying.ports.host_rd_data)

        self.wire(self.ports.cgra_to_io_stall,\
                self.underlying.ports.cgra_to_io_stall)
        self.wire(self.ports.cgra_to_io_wr_en,\
                self.underlying.ports.cgra_to_io_wr_en)
        self.wire(self.ports.cgra_to_io_rd_en,\
                self.underlying.ports.cgra_to_io_rd_en)
        self.wire(self.ports.io_to_cgra_rd_data_valid,\
                self.underlying.ports.io_to_cgra_rd_data_valid)
        self.wire(self.ports.cgra_to_io_wr_data,\
                self.underlying.ports.cgra_to_io_wr_data)
        self.wire(self.ports.io_to_cgra_rd_data,\
                self.underlying.ports.io_to_cgra_rd_data)
        self.wire(self.ports.cgra_to_io_addr_high,\
                self.underlying.ports.cgra_to_io_addr_high)
        self.wire(self.ports.cgra_to_io_addr_low,\
                self.underlying.ports.cgra_to_io_addr_low)

        self.wire(self.ports.glb_to_cgra_cfg_wr,\
                self.underlying.ports.glb_to_cgra_cfg_wr)
        self.wire(self.ports.glb_to_cgra_cfg_addr,\
                self.underlying.ports.glb_to_cgra_cfg_addr)
        self.wire(self.ports.glb_to_cgra_cfg_data,\
                self.underlying.ports.glb_to_cgra_cfg_data)

        self.wire(self.ports.glc_to_io_stall,\
                self.underlying.ports.glc_to_io_stall)
        self.wire(self.ports.glc_to_cgra_cfg_wr,\
                self.underlying.ports.glc_to_cgra_cfg_wr)
        self.wire(self.ports.glc_to_cgra_cfg_addr,\
                self.underlying.ports.glc_to_cgra_cfg_addr)
        self.wire(self.ports.glc_to_cgra_cfg_data,\
                self.underlying.ports.glc_to_cgra_cfg_data)

        self.wire(self.ports.cgra_start_pulse,\
                self.underlying.ports.cgra_start_pulse)
        self.wire(self.ports.config_start_pulse,\
                self.underlying.ports.config_start_pulse)
        self.wire(self.ports.config_done_pulse,\
                self.underlying.ports.config_done_pulse)

        self.wire(self.ports.glb_config.write[0],\
                self.underlying.ports.glb_config_wr)
        self.wire(self.ports.glb_config.read[0],\
                self.underlying.ports.glb_config_rd)
        self.wire(self.ports.glb_config.config_data,\
                self.underlying.ports.glb_config_wr_data)
        self.wire(self.ports.glb_config.config_addr,\
                self.underlying.ports.glb_config_addr)
        self.wire(self.ports.glb_config_rd_data,\
                self.underlying.ports.glb_config_rd_data)

        self.wire(self.ports.top_config.write[0],\
                self.underlying.ports.top_config_wr)
        self.wire(self.ports.top_config.read[0],\
                self.underlying.ports.top_config_rd)
        self.wire(self.ports.top_config.config_data,\
                self.underlying.ports.top_config_wr_data)
        self.wire(self.ports.top_config.config_addr,\
                self.underlying.ports.top_config_addr)
        self.wire(self.ports.top_config_rd_data,\
                self.underlying.ports.top_config_rd_data)

    def name(self):
        return f"GlobalBuffer_{self.num_banks}_{self.bank_addr_width}_"\
                "{self.bank_data_width}_{self.cgra_data_width}_{self.num_io}_{self.num_cfg}"
