import magma
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.const import Const
from gemstone.generator.from_verilog import FromVerilog
from gemstone.generator.generator import Generator
from . import global_buffer_genesis2
import math


class GlobalBuffer(Generator):
    def __init__(self, num_banks=32, bank_addr=17, bank_data=64,\
            num_io=8, num_cfg=8, num_cols=32, cgra_data=16, top_cfg_addr=12,\
            cfg_addr=32, cfg_data=32):
        super().__init__()

        self.num_banks = num_banks
        self.bank_data = bank_data
        self.bank_addr = bank_addr
        self.glb_addr_width = math.ceil(math.log2(self.num_banks))\
                + self.bank_addr
        self.num_io = num_io
        self.num_cfg = num_cfg
        self.num_cols = num_cols
        self.cgra_data = cgra_data
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

            host_wr_en=magma.In(magma.Bit),
            host_wr_addr=magma.In(magma.Bits[self.glb_addr_width]),
            host_wr_data=magma.In(magma.Bits[self.bank_data]),

            host_rd_en=magma.In(magma.Bit),
            host_rd_addr=magma.In(magma.Bits[self.glb_addr_width]),
            host_rd_data=magma.Out(magma.Bits[self.bank_data]),

            #cgra_to_io_stall=magma.In(magma.Array[self.num_io, magma.Bits[1]]),
            cgra_to_io_wr_en=magma.In(magma.Array[self.num_io, magma.Bits[1]]),
            cgra_to_io_rd_en=magma.In(magma.Array[self.num_io, magma.Bits[1]]),
            io_to_cgra_rd_data_valid=magma.Out(magma.Array[self.num_io, magma.Bits[1]]),
            cgra_to_io_wr_data=magma.In(\
                    magma.Array[self.num_io, magma.Bits[self.cgra_data]]),
            io_to_cgra_rd_data=magma.Out(\
                    magma.Array[self.num_io, magma.Bits[self.cgra_data]]),
            cgra_to_io_addr_high=magma.In(\
                    magma.Array[self.num_io, magma.Bits[self.cgra_data]]),
            cgra_to_io_addr_low=magma.In(\
                    magma.Array[self.num_io, magma.Bits[self.cgra_data]]),

            glb_to_cgra_cfg_wr=magma.Out(\
                    magma.Array[self.num_cols, magma.Bits[1]]),
            glb_to_cgra_cfg_addr=magma.Out(\
                    magma.Array[self.num_cols, magma.Bits[self.cfg_addr]]),
            glb_to_cgra_cfg_data=magma.Out(\
                    magma.Array[self.num_cols, magma.Bits[self.cfg_data]]),

            glc_to_io_stall=magma.In(magma.Bit),
            glc_to_cgra_cfg_wr=magma.In(magma.Bit),
            glc_to_cgra_cfg_addr=magma.In(magma.Bits[self.cfg_addr]),
            glc_to_cgra_cfg_data=magma.In(magma.Bits[self.cfg_data]),

            cgra_start_pulse=magma.In(magma.Bit),
            config_start_pulse=magma.In(magma.Bit),
            config_done_pulse=magma.Out(magma.Bit),

            glb_config=magma.In(self.glb_config_type),
            glb_config_rd_data=magma.Out(magma.Bits[self.cfg_data]),

            top_config=magma.In(self.top_config_type),
            top_config_rd_data=magma.Out(magma.Bits[self.cfg_data])
        )

        self.underlying = FromVerilog("global_buffer/verilog/global_buffer_flatten.sv")

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

        for i in range(self.num_io):
            #self.wire(self.ports.cgra_to_io_stall[i][0],\
            #        self.underlying.ports.cgra_to_io_stall[i])
            self.wire(self.ports.cgra_to_io_wr_en[i][0],\
                    self.underlying.ports.cgra_to_io_wr_en[i])
            self.wire(self.ports.cgra_to_io_rd_en[i][0],\
                    self.underlying.ports.cgra_to_io_rd_en[i])
            self.wire(self.ports.io_to_cgra_rd_data_valid[i][0],\
                    self.underlying.ports.io_to_cgra_rd_data_valid[i])
            self.wire(self.ports.cgra_to_io_wr_data[i],\
                    self.underlying.ports.cgra_to_io_wr_data[i*self.cgra_data:\
                    (i+1)*self.cgra_data])
            self.wire(self.ports.io_to_cgra_rd_data[i],\
                    self.underlying.ports.io_to_cgra_rd_data[i*self.cgra_data:\
                    (i+1)*self.cgra_data])
            self.wire(self.ports.cgra_to_io_addr_high[i],\
                    self.underlying.ports.cgra_to_io_addr_high[i*self.cgra_data:\
                    (i+1)*self.cgra_data])
            self.wire(self.ports.cgra_to_io_addr_low[i],\
                    self.underlying.ports.cgra_to_io_addr_low[i*self.cgra_data:\
                    (i+1)*self.cgra_data])

        for i in range(self.num_cols):
            self.wire(self.ports.glb_to_cgra_cfg_wr[i][0],\
                    self.underlying.ports.glb_to_cgra_cfg_wr[i])
            self.wire(self.ports.glb_to_cgra_cfg_addr[i],\
                    self.underlying.ports.glb_to_cgra_cfg_addr[i*self.cfg_addr:\
                    (i+1)*self.cfg_addr])
            self.wire(self.ports.glb_to_cgra_cfg_data[i],\
                    self.underlying.ports.glb_to_cgra_cfg_data[i*self.cfg_data:\
                    (i+1)*self.cfg_data])


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
        return f"GlobalBuffer_{self.num_banks}_{self.bank_addr}_"\
                f"{self.num_io}_{self.num_cfg}_"\
                f"{self.num_cols}_{self.top_cfg_addr}"
