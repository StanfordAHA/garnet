/*==============================================================================
** Module: test_address_generator.cpp
** Description: Test driver for address generator
** Author: Taeyoung Kong
** Change history: 05/11/2019 - Implement first version of address generator
**                              test driver
** NOTE:    Word size is 16bit.
**          Address should be word-aligned.
**          This does not support unaligned access.
**============================================================================*/

#include "Vaddress_generator.h"
#include "verilated.h"
#include "testbench.h"
#include "time.h"
#include <verilated_vcd_c.h>
#include <vector>
#include <random>
#include <string.h>

#define MAX_WORD 16

#define DEBUG

// Address is byte addressable
uint16_t GLB_ADDR_WIDTH = 22;
uint16_t BANK_DATA_WIDTH = 64;
uint16_t CGRA_DATA_WIDTH = 16;

using namespace std;

uint16_t* glb;

typedef enum MODE
{
    IDLE        = 0,
    INSTREAM    = 1,
    OUTSTREAM   = 2,
    SRAM        = 3
} MODE;

class ADDR_GEN_TB : public TESTBENCH<Vaddress_generator> {
public:
    uint8_t io_to_bank_rd_en_d1;
    uint32_t io_to_bank_addr_d1;

    ADDR_GEN_TB(void) {
        m_dut->clk_en = 1;
        io_to_bank_rd_en_d1 = 0;
        io_to_bank_addr_d1 = 0;
        reset();
    }

    ~ADDR_GEN_TB(void) {}

    void tick() {
        m_tickcount++;

        // All combinational logic should be settled
        // before we tick the clock
        eval();
        if(m_trace) m_trace->dump(10*m_tickcount-4);

        // Toggle the clock
        // Rising edge
        m_dut->clk = 1;

        // bank_to_io_rd_data is from glb stub with one cycle latency
        if (m_dut->clk_en != 0) {
            if (io_to_bank_rd_en_d1 == 1) {
                m_dut->bank_to_io_rd_data = ((uint64_t) glb[(io_to_bank_addr_d1>>1)+3] << 48)
                                          + ((uint64_t) glb[(io_to_bank_addr_d1>>1)+2] << 32)
                                          + ((uint64_t) glb[(io_to_bank_addr_d1>>1)+1] << 16)
                                          + ((uint64_t) glb[(io_to_bank_addr_d1>>1)+0]);
            }
            io_to_bank_rd_en_d1 = m_dut->io_to_bank_rd_en;
            io_to_bank_addr_d1 = m_dut->io_to_bank_addr;
        }

        if (m_dut->io_to_bank_wr_en == 1) {
            glb[((m_dut->io_to_bank_addr>>3)<<2)+0] = (uint16_t) ((m_dut->io_to_bank_wr_data & 0x000000FF) & (m_dut->io_to_bank_wr_data_bit_sel & 0x000000FF));
            glb[((m_dut->io_to_bank_addr>>3)<<2)+1] = (uint16_t) (((m_dut->io_to_bank_wr_data & 0x0000FF00) & (m_dut->io_to_bank_wr_data_bit_sel & 0x0000FF00)) >> 16);
            glb[((m_dut->io_to_bank_addr>>3)<<2)+2] = (uint16_t) (((m_dut->io_to_bank_wr_data & 0x00FF0000) & (m_dut->io_to_bank_wr_data_bit_sel & 0x00FF0000)) >> 32);
            glb[((m_dut->io_to_bank_addr>>3)<<2)+3] = (uint16_t) (((m_dut->io_to_bank_wr_data & 0xFF000000) & (m_dut->io_to_bank_wr_data_bit_sel & 0xFF000000)) >> 48);
        }

        m_dut->eval();
        if(m_trace) m_trace->dump(10*m_tickcount);

        // Falling edge
        m_dut->clk = 0;
        m_dut->eval();
        if(m_trace) {
            m_trace->dump(10*m_tickcount+5);
            m_trace->flush();
        }
    }

    void instream_test(uint32_t num_words, uint32_t start_addr, uint32_t stall_cycle=0) {
        // address must be word aligned
        if (start_addr % 2 != 0) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Address is not word aligned" << std::endl;
            m_trace->close();
            exit(EXIT_FAILURE);
        }
        set_start_addr(start_addr);
        set_num_words(num_words);
        set_mode(INSTREAM);
        m_dut->cgra_start_pulse = 1;
        tick();
        m_dut->cgra_start_pulse = 0;
        uint32_t int_addr = start_addr;
        uint32_t int_addr_next = start_addr;
        uint32_t num_cnt = 0;
        uint32_t stall_cnt = 0;
        int stall_time = -1;
        // one cycle latency
        tick();

        // if stall_cycle is non-zero, randomly stall at stall_time to test stall
        if (stall_cycle != 0 && num_words > 0) {
            stall_cnt = stall_cycle;
            stall_time = min((rand() % num_words), (uint32_t)1);
        }

        printf("Address generator is INSTREAM mode.\n Start feeding data\n");
        // READ state
        while (num_cnt < num_words) {
            if (num_cnt == stall_time && stall_cnt > 0)  {
                m_dut->clk_en = 0;
                stall_cnt--;
                int_addr = int_addr;
                int_addr_next = int_addr_next;
            }
            else {
                m_dut->clk_en = 1;
                num_cnt++;
                int_addr = int_addr_next;
                int_addr_next += 2;
            }
            tick();
            printf("Address generator is streaming data to CGRA.\n");
            printf("\tData: 0x%04x / Addr: 0x%08x / Valid: %01d\n", m_dut->io_to_cgra_rd_data, int_addr, m_dut->io_to_cgra_rd_data_valid);
            my_assert(m_dut->io_to_cgra_rd_data, glb[(int_addr>>1)], "io_to_cgra_rd_data");
            my_assert(m_dut->io_to_cgra_rd_data_valid, 1, "io_to_cgra_rd_data_valid");
        }
        printf("End feeding data\n");
        for (uint32_t t=0; t<10; t++) {
            tick();
            my_assert(m_dut->io_to_cgra_rd_data_valid, 0, "io_to_cgra_rd_data_valid");
        }
    }

    void outstream_test_sequential(uint32_t num_words, uint32_t start_addr, uint32_t stall_cycle=0) {
        // address must be word aligned
        if (start_addr % 2 != 0) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Address is not word aligned" << std::endl;
            m_trace->close();
            exit(EXIT_FAILURE);
        }
        set_start_addr(start_addr);
        set_num_words(num_words);
        set_mode(OUTSTREAM);
        m_dut->cgra_start_pulse = 1;
        tick();
        m_dut->cgra_start_pulse = 0;
        uint32_t int_addr = start_addr;
        uint32_t int_addr_next = start_addr;
        uint32_t stall_cnt = 0;
        int stall_time = -1;
        // one cycle latency

        // if stall_cycle is non-zero, randomly stall at stall_time to test stall
        if (stall_cycle != 0 && num_words > 0) {
            stall_cnt = stall_cycle;
            stall_time = min((rand() % num_words), (uint32_t)1);
        }

        printf("Address generator is OUTSTREAM mode.\n Start writing data\n");
        while (
        for (uint32_t t=0; t<(num_words + stall_cnt); t++) {
            if (t >= stall_time && t < stall_time + stall_cnt)  m_dut->clk_en = 0;
            else m_dut->clk_en = 1;
            if (m_dut->clk_en == 1) {
                int_addr = int_addr_next;
                int_addr_next += 2;
            }
            else {
                int_addr = int_addr;
                int_addr_next = int_addr_next;
            }
            tick();
            printf("Address generator is streaming data to CGRA.\n");
            printf("\tData: 0x%04x / Addr: 0x%08x / Valid: %01d\n", m_dut->io_to_cgra_rd_data, int_addr, m_dut->io_to_cgra_rd_data_valid);
            my_assert(m_dut->io_to_cgra_rd_data, glb[(int_addr>>1)], "io_to_cgra_rd_data");
            my_assert(m_dut->io_to_cgra_rd_data_valid, 1, "io_to_cgra_rd_data_valid");
        }
        printf("End feeding data\n");
        for (uint32_t t=0; t<10; t++) {
            tick();
            my_assert(m_dut->io_to_cgra_rd_data_valid, 0, "io_to_cgra_rd_data_valid");
        }
    }

    void outstream_test_random(uint32_t num_words, uint32_t start_addr) {
    }

private:
    void set_start_addr(uint32_t start_addr) {
        m_dut->start_addr = start_addr;
    }

    void set_num_words(uint32_t num_words) {
        m_dut->num_words = num_words;
    }

    void set_mode(MODE mode) {
        m_dut->mode = mode;
    }

    void stall(uint32_t cycle) {
        m_dut->clk_en = 0;
        for(uint32_t i=0; i<cycle; i++)
            tick();
        m_dut->clk_en = 1;
    }
};

int main(int argc, char **argv) {
    int rcode = EXIT_SUCCESS;
    if (argc % 2 == 0) {
        printf("\nParameter wrong!\n");
        return 0;
    }
    size_t pos;
    for (int i = 1; i < argc; i=i+2) {
        string argv_tmp = argv[i];
        if (argv_tmp == "GLB_ADDR_WIDTH") {
            GLB_ADDR_WIDTH = stoi(argv[i+1], &pos);
        }
        else if (argv_tmp == "BANK_DATA_WIDTH") {
            BANK_DATA_WIDTH = stoi(argv[i+1], &pos);
        }
        else if (argv_tmp == "CGRA_DATA_WIDTH") {
            CGRA_DATA_WIDTH = stoi(argv[i+1], &pos);
        }
        else {
            printf("\nParameter wrong!\n");
            return 0;
        }
    }

    srand (time(NULL));
    // Instantiate address generator testbench
    ADDR_GEN_TB *addr_gen = new ADDR_GEN_TB();
    addr_gen->opentrace("trace_addr_gen.vcd");
    addr_gen->reset();

    // Create global buffer stub using array
    glb = new uint16_t[1<<(GLB_ADDR_WIDTH-1)];

    // initialize glb with random 16bit number
    for (uint32_t i=0; i<(1<<(GLB_ADDR_WIDTH-1)); i++) {
            glb[i]= (uint16_t)rand();
    }

    addr_gen->instream_test(110, 402);

    printf("\nAll simulations are passed!\n");
    exit(rcode);
}

