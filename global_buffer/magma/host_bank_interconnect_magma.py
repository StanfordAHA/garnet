import magma as m
import mantle
from gemstone.generator.generator import Generator
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.const import Const
from gemstone.common.mux_wrapper import MuxWrapper

GLB_ADDR_WIDTH = 32
BANK_ADDR_WIDTH = 17
BANK_DATA_WIDTH = 64

class HostBankInterconnect(Generator):
    def __init__(self, num_banks):

        self.num_banks = num_banks
        super().__init__()

        self.add_ports(
            clk=m.In(m.Clock),
            reset=m.In(m.AsyncReset),

            # host write
            host_wr_en=m.In(m.Bits[1]),
            host_wr_strb=m.In(m.Bits[int(BANK_DATA_WIDTH/8)]),
            host_wr_data=m.In(m.Bits[BANK_DATA_WIDTH]),
            host_wr_addr=m.In(m.Bits[GLB_ADDR_WIDTH]),

            # host read
            host_rd_en=m.In(m.Bits[1]),
            host_rd_addr=m.In(m.Bits[GLB_ADDR_WIDTH]),
            host_rd_data=m.Out(m.Bits[BANK_DATA_WIDTH]),

            # host to bank
            host_to_bank_wr_en=m.Out(m.Array[self.num_banks, m.Bits[1]]),
            host_to_bank_wr_data=m.Out(m.Array[self.num_banks, m.Bits[BANK_DATA_WIDTH]]),
            host_to_bank_wr_data_bit_sel=m.Out(m.Array[self.num_banks, m.Bits[BANK_DATA_WIDTH]]),
            host_to_bank_wr_addr=m.Out(m.Array[self.num_banks, m.Bits[BANK_ADDR_WIDTH]]),

            host_to_bank_rd_en=m.Out(m.Array[self.num_banks, m.Bits[1]]),
            host_to_bank_rd_addr=m.Out(m.Array[self.num_banks, m.Bits[BANK_ADDR_WIDTH]]),
            bank_to_host_rd_data=m.In(m.Array[self.num_banks, m.Bits[BANK_DATA_WIDTH]]),
        )

        # host wr_en
        int_host_wr_en=[m.Bit]*self.num_banks
        for i in range(self.num_banks):
            eq = FromMagma(mantle.DefineEQ(5))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(Const(i), eq.ports.I0)
            self.wire(self.ports.host_wr_addr[BANK_ADDR_WIDTH:BANK_ADDR_WIDTH+5], eq.ports.I1)
            self.wire(and_.ports.I1[0], eq.ports.O)
            self.wire(and_.ports.I0, self.ports.host_wr_en)
            int_host_wr_en[i]=and_.ports.O[0]

        # wr_en pipeline
        int_host_wr_en_d1 = [m.Bit]*self.num_banks
        for i in range(self.num_banks):
            pipeline_reg_d1 = FromMagma(mantle.DefineRegister(1, has_ce=False, has_async_reset=False))
            self.wire(self.ports.clk, pipeline_reg_d1.ports.clk)
            self.wire(int_host_wr_en[i], pipeline_reg_d1.ports.I[0])
            int_host_wr_en_d1[i] = pipeline_reg_d1.ports.O[0]

        # wr_addr pipeline
        int_host_wr_addr_d1 = [m.Bits[BANK_ADDR_WIDTH]]*self.num_banks
        for i in range(self.num_banks):
            pipeline_reg_d1 = FromMagma(mantle.DefineRegister(BANK_ADDR_WIDTH, has_ce=False, has_async_reset=False))
            self.wire(self.ports.clk, pipeline_reg_d1.ports.clk)
            self.wire(self.ports.host_wr_addr[0:BANK_ADDR_WIDTH], pipeline_reg_d1.ports.I)
            int_host_wr_addr_d1[i] = pipeline_reg_d1.ports.O

        # wr_data pipeline
        int_host_wr_data_d1 = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        for i in range(self.num_banks):
            pipeline_reg_d1 = FromMagma(mantle.DefineRegister(BANK_DATA_WIDTH, has_ce=False, has_async_reset=False))
            self.wire(self.ports.clk, pipeline_reg_d1.ports.clk)
            self.wire(self.ports.host_wr_data, pipeline_reg_d1.ports.I)
            int_host_wr_data_d1[i] = pipeline_reg_d1.ports.O

        # wr_strb pipeline
        int_host_wr_strb_d1 = [m.Bits[int(BANK_DATA_WIDTH/8)]]*self.num_banks
        for i in range(self.num_banks):
            pipeline_reg_d1 = FromMagma(mantle.DefineRegister(int(BANK_DATA_WIDTH/8), has_ce=False, has_async_reset=False))
            self.wire(self.ports.clk, pipeline_reg_d1.ports.clk)
            self.wire(self.ports.host_wr_strb, pipeline_reg_d1.ports.I)
            int_host_wr_strb_d1[i] = pipeline_reg_d1.ports.O

        # output to bank assignment
        for i in range(self.num_banks):
            self.wire(self.ports.host_to_bank_wr_en[i][0], int_host_wr_en_d1[i])
            self.wire(self.ports.host_to_bank_wr_data[i], int_host_wr_data_d1[i])
            self.wire(self.ports.host_to_bank_wr_addr[i], int_host_wr_addr_d1[i])
            for j in range(BANK_DATA_WIDTH):
                self.wire(self.ports.host_to_bank_wr_data_bit_sel[i][j], int_host_wr_strb_d1[i][int(j/8)])

        # host rd_en and host-to-bank rd_en
        for i in range(self.num_banks):
            eq = FromMagma(mantle.DefineEQ(5))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(Const(i), eq.ports.I0)
            self.wire(self.ports.host_rd_addr[BANK_ADDR_WIDTH:BANK_ADDR_WIDTH+5], eq.ports.I1)
            self.wire(and_.ports.I1[0], eq.ports.O)
            self.wire(and_.ports.I0, self.ports.host_rd_en)
            self.wire(self.ports.host_to_bank_rd_en[i], and_.ports.O)

        # host-to-bank rd_addr
        for i in range(self.num_banks):
            self.wire(self.ports.host_to_bank_rd_addr[i], self.ports.host_rd_addr[0:BANK_ADDR_WIDTH])

        # rd_en_d2 pipeline
        pipeline_reg_d1 = FromMagma(mantle.DefineRegister(1, has_ce=False, has_async_reset=False))
        self.wire(self.ports.clk, pipeline_reg_d1.ports.clk)
        self.wire(self.ports.host_rd_en, pipeline_reg_d1.ports.I)
        pipeline_reg_d2 = FromMagma(mantle.DefineRegister(1, has_ce=False, has_async_reset=False))
        self.wire(self.ports.clk, pipeline_reg_d2.ports.clk)
        self.wire(pipeline_reg_d1.ports.O, pipeline_reg_d2.ports.I)
        host_rd_en_d2 = pipeline_reg_d2.ports.O

        # bank_sel_d2 pipeline
        pipeline_reg_d1 = FromMagma(mantle.DefineRegister(5, has_ce=False, has_async_reset=False))
        self.wire(self.ports.clk, pipeline_reg_d1.ports.clk)
        self.wire(self.ports.host_rd_addr[BANK_ADDR_WIDTH:BANK_ADDR_WIDTH+5], pipeline_reg_d1.ports.I)
        pipeline_reg_d2 = FromMagma(mantle.DefineRegister(5, has_ce=False, has_async_reset=False))
        self.wire(self.ports.clk, pipeline_reg_d2.ports.clk)
        self.wire(pipeline_reg_d1.ports.O, pipeline_reg_d2.ports.I)
        int_host_rd_bank_sel_d2 = pipeline_reg_d2.ports.O

        # bank_to_host_rd_data pipeline
        int_host_rd_data_d1 = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        for i in range(self.num_banks):
            pipeline_reg_d1 = FromMagma(mantle.DefineRegister(BANK_DATA_WIDTH, has_ce=False, has_async_reset=False))
            self.wire(self.ports.clk, pipeline_reg_d1.ports.clk)
            self.wire(self.ports.bank_to_host_rd_data[i], pipeline_reg_d1.ports.I)
            int_host_rd_data_d1[i] = pipeline_reg_d1.ports.O

        # int_host_rd_data
        mux = MuxWrapper(self.num_banks, 64,)
        for i in range(self.num_banks):
            self.wire(int_host_rd_data_d1[i], mux.ports.I[i])
        self.wire(int_host_rd_bank_sel_d2, mux.ports.S)
        int_host_rd_data = mux.ports.O

        # host_rd_data
        rd_data_reg = FromMagma(mantle.DefineRegister(BANK_DATA_WIDTH, has_ce=False, has_async_reset=True))
        eq = FromMagma(mantle.DefineEQ(1))
        mux = MuxWrapper(2, 64,)
        self.wire(Const(1), eq.ports.I0)
        self.wire(host_rd_en_d2, eq.ports.I1)
        self.wire(eq.ports.O, mux.ports.S[0])
        self.wire(rd_data_reg.ports.O, mux.ports.I[0])
        self.wire(int_host_rd_data, mux.ports.I[1])
        self.wire(self.ports.host_rd_data, mux.ports.O)

        # rd_data reg
        self.wire(self.ports.clk, rd_data_reg.ports.clk)
        self.wire(mux.ports.O, rd_data_reg.ports.I)


    def name(self):
        return f"HostBankInterconnect_{self.num_banks}"
