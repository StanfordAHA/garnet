import magma
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.const import Const
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.generator import Generator
from . import global_buffer_genesis2
from global_buffer.soc_data_type import SoCDataType


class GlobalBuffer(Generator):
    def __init__(self, num_banks, num_io, num_cfg, bank_addr_width,
                 glb_addr_width=32, cfg_addr_width=32, cfg_data_width=32,
                 axi_addr_width=12):
        super().__init__()

        self.num_banks = num_banks
        self.bank_addr_width = bank_addr_width
        self.glb_addr_width = glb_addr_width
        self.num_io = num_io
        self.num_cfg = num_cfg
        self.bank_data = 64
        self.cgra_data = 16
        self.cfg_addr_width = cfg_addr_width
        self.cfg_data_width = cfg_data_width
        self.axi_addr_width = axi_addr_width

        self.config_type = ConfigurationType(self.cfg_addr_width,
                                             self.cfg_data_width)
        self.axi_config_type = ConfigurationType(self.axi_addr_width,
                                                 self.cfg_data_width)

        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),

            soc_data=SoCDataType(self.glb_addr_width, self.bank_data),
            cgra_to_io_wr_en=magma.In(magma.Array[self.num_io, magma.Bit]),
            cgra_to_io_rd_en=magma.In(magma.Array[self.num_io, magma.Bit]),
            io_to_cgra_rd_data_valid=magma.Out(
                magma.Array[self.num_io, magma.Bit]),
            cgra_to_io_wr_data=magma.In(
                magma.Array[self.num_io, magma.Bits[self.cgra_data]]),
            io_to_cgra_rd_data=magma.Out(
                magma.Array[self.num_io, magma.Bits[self.cgra_data]]),
            cgra_to_io_addr_high=magma.In(
                magma.Array[self.num_io, magma.Bits[self.cgra_data]]),
            cgra_to_io_addr_low=magma.In(
                magma.Array[self.num_io, magma.Bits[self.cgra_data]]),

            glc_to_io_stall=magma.In(magma.Bit),

            cgra_start_pulse=magma.In(magma.Bit),
            cgra_done_pulse=magma.Out(magma.Bit),
            config_start_pulse=magma.In(magma.Bit),
            config_done_pulse=magma.Out(magma.Bit),

            cgra_config=magma.In(self.config_type),
            glb_to_cgra_config=magma.Out(
                magma.Array[self.num_cfg, self.config_type]),

            glb_config=magma.In(self.axi_config_type),
            glb_config_rd_data=magma.Out(magma.Bits[self.cfg_data_width]),
            glb_sram_config=magma.In(self.config_type),
            glb_sram_config_rd_data=magma.Out(magma.Bits[self.cfg_data_width])
        )

        wrapper = global_buffer_genesis2.glb_wrapper
        param_mapping = global_buffer_genesis2.param_mapping
        generator = wrapper.generator(param_mapping, mode="declare")
        circ = generator(num_banks=self.num_banks,
                         num_io=self.num_io,
                         num_cfg=self.num_cfg,
                         bank_addr_width=self.bank_addr_width,
                         cfg_addr_width=self.cfg_addr_width,
                         cfg_data=self.cfg_data_width)
        self.underlying = FromMagma(circ)

        self.wire(self.ports.clk, self.underlying.ports.clk)
        self.wire(self.ports.reset, self.underlying.ports.reset)

        self.wire(self.ports.soc_data.wr_strb,
                  self.underlying.ports.host_wr_strb)
        self.wire(self.ports.soc_data.wr_addr,
                  self.underlying.ports.host_wr_addr)
        self.wire(self.ports.soc_data.wr_data,
                  self.underlying.ports.host_wr_data)

        self.wire(self.ports.soc_data.rd_en,
                  self.underlying.ports.host_rd_en)
        self.wire(self.ports.soc_data.rd_addr,
                  self.underlying.ports.host_rd_addr)
        self.wire(self.ports.soc_data.rd_data,
                  self.underlying.ports.host_rd_data)

        for i in range(self.num_io):
            self.wire(self.ports.cgra_to_io_wr_en[i],
                      self.underlying.ports.cgra_to_io_wr_en[i])
            self.wire(self.ports.cgra_to_io_rd_en[i],
                      self.underlying.ports.cgra_to_io_rd_en[i])
            self.wire(self.ports.io_to_cgra_rd_data_valid[i],
                      self.underlying.ports.io_to_cgra_rd_data_valid[i])
            self.wire(self.ports.cgra_to_io_wr_data[i],
                      self.underlying.ports.cgra_to_io_wr_data[
                          i * self.cgra_data:(i + 1) * self.cgra_data])
            self.wire(self.ports.io_to_cgra_rd_data[i],
                      self.underlying.ports.io_to_cgra_rd_data[
                          i * self.cgra_data:(i + 1) * self.cgra_data])
            self.wire(self.ports.cgra_to_io_addr_high[i],
                      self.underlying.ports.cgra_to_io_addr_high[
                          i * self.cgra_data:(i + 1) * self.cgra_data])
            self.wire(self.ports.cgra_to_io_addr_low[i],
                      self.underlying.ports.cgra_to_io_addr_low[
                          i * self.cgra_data:(i + 1) * self.cgra_data])

        for i in range(self.num_cfg):
            self.wire(self.ports.glb_to_cgra_config[i].write[0],
                      self.underlying.ports.glb_to_cgra_cfg_wr[i])
            self.wire(self.ports.glb_to_cgra_config[i].read[0],
                      self.underlying.ports.glb_to_cgra_cfg_rd[i])
            self.wire(self.ports.glb_to_cgra_config[i].config_addr,
                      self.underlying.ports.glb_to_cgra_cfg_addr[
                          i * self.cfg_addr_width:
                          (i + 1) * self.cfg_addr_width])
            self.wire(self.ports.glb_to_cgra_config[i].config_data,
                      self.underlying.ports.glb_to_cgra_cfg_data[
                          i * self.cfg_data_width:
                          (i + 1) * self.cfg_data_width])

        self.wire(self.ports.glc_to_io_stall,
                  self.underlying.ports.glc_to_io_stall)

        self.wire(self.ports.cgra_config.write[0],
                  self.underlying.ports.glc_to_cgra_cfg_wr)
        self.wire(self.ports.cgra_config.read[0],
                  self.underlying.ports.glc_to_cgra_cfg_rd)
        self.wire(self.ports.cgra_config.config_addr,
                  self.underlying.ports.glc_to_cgra_cfg_addr)
        self.wire(self.ports.cgra_config.config_data,
                  self.underlying.ports.glc_to_cgra_cfg_data)

        self.wire(self.ports.cgra_start_pulse,
                  self.underlying.ports.cgra_start_pulse)
        self.wire(self.ports.cgra_done_pulse,
                  self.underlying.ports.cgra_done_pulse)
        self.wire(self.ports.config_start_pulse,
                  self.underlying.ports.config_start_pulse)
        self.wire(self.ports.config_done_pulse,
                  self.underlying.ports.config_done_pulse)

        self.wire(self.ports.glb_config.write[0],
                  self.underlying.ports.glb_config_wr)
        self.wire(self.ports.glb_config.read[0],
                  self.underlying.ports.glb_config_rd)
        self.wire(self.ports.glb_config.config_data,
                  self.underlying.ports.glb_config_wr_data)
        self.wire(self.ports.glb_config.config_addr,
                  self.underlying.ports.glb_config_addr)
        self.wire(self.ports.glb_config_rd_data,
                  self.underlying.ports.glb_config_rd_data)

        self.wire(self.ports.glb_sram_config.write[0],
                  self.underlying.ports.glb_sram_config_wr)
        self.wire(self.ports.glb_sram_config.read[0],
                  self.underlying.ports.glb_sram_config_rd)
        self.wire(self.ports.glb_sram_config.config_data,
                  self.underlying.ports.glb_sram_config_wr_data)
        self.wire(self.ports.glb_sram_config.config_addr,
                  self.underlying.ports.glb_sram_config_addr)
        self.wire(self.ports.glb_sram_config_rd_data,
                  self.underlying.ports.glb_sram_config_rd_data)

    def name(self):
        return f"GlobalBuffer"
