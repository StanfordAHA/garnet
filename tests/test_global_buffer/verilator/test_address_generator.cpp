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
        glb_update();
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
            }
            else {
                m_dut->clk_en = 1;
            }

            tick();

            printf("Address generator is streaming data to CGRA.\n");
            if (m_dut->clk_en == 0) printf("CGRA is stalled now\n");
            printf("\tData: 0x%04x / Addr: 0x%08x / Valid: %01d\n", m_dut->io_to_cgra_rd_data, int_addr, m_dut->io_to_cgra_rd_data_valid);
            my_assert(m_dut->io_to_cgra_rd_data, glb[(int_addr>>1)], "io_to_cgra_rd_data");
            my_assert(m_dut->io_to_cgra_rd_data_valid, 1, "io_to_cgra_rd_data_valid");

            // update for next read
            if (m_dut->clk_en == 1) {
                num_cnt++;
                int_addr += 2;
            }
        }

        printf("End feeding data\n");
        
        for (uint32_t t=0; t<10; t++) {
            tick();
            my_assert(m_dut->io_to_cgra_rd_data_valid, 0, "io_to_cgra_rd_data_valid");
        }
    }

    void outstream_test(uint32_t num_words, uint32_t start_addr, uint32_t stall_cycle=0) {
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
        uint32_t num_cnt = 0;
        uint32_t stall_cnt = 0;
        int stall_time = -1;

        // if stall_cycle is non-zero, randomly stall at stall_time to test stall
        if (stall_cycle != 0 && num_words > 0) {
            stall_cnt = stall_cycle;
            stall_time = min((rand() % num_words), (uint32_t)1);
        }

        printf("Address generator is OUTSTREAM mode.\n Start writing data\n");

        // 1 cycle delay
        tick();

        // Create random wr_data_array that would be generated from CGRA
        // This array will be used to check whether they are correctly stored
        // in GLB
        uint16_t* wr_data_array = new uint16_t[num_words];
        for (uint32_t i=0; i<num_words; i++)
            wr_data_array[i] = (uint16_t)rand();

        // Since this is sequential test, wr_en stays high
        m_dut->cgra_to_io_wr_en = rand() % 2;

        // Write state
        m_dut->cgra_to_io_wr_data = wr_data_array[num_cnt];
        while (num_cnt < num_words) {
            if (num_cnt == stall_time && stall_cnt > 0)  {
                m_dut->clk_en = 0;
                stall_cnt--;
            }
            else {
                m_dut->clk_en = 1;
            }
            tick();

            printf("CGRA is writing data to IO controller.\n");
            if (m_dut->clk_en == 0) printf("CGRA is stalled now\n");
            printf("\tData: 0x%04x / Addr: 0x%08x / Valid: %01d\n", m_dut->cgra_to_io_wr_data, int_addr, m_dut->cgra_to_io_wr_en);

            // update for next write
            if (m_dut->clk_en == 1) {
                if (m_dut->cgra_to_io_wr_en) {
                    int_addr += 2;
                    num_cnt++;
                }
                m_dut->cgra_to_io_wr_en = rand() % 2;
                m_dut->cgra_to_io_wr_data = wr_data_array[num_cnt];
            }
        }

        m_dut->cgra_to_io_wr_en = 0;
        printf("End writing data\n");

        tick();
        my_assert(m_dut->cgra_done_pulse, 1, "cgra_done_pulse");
        for (uint32_t t=0; t<10; t++) {
            tick();
            my_assert(m_dut->cgra_done_pulse, 0, "cgra_done_pulse");
        }
        // This assertion checks whether all data are stored in glb
        // Due to data width difference, we cannnot check assertion everytime when CGRA writes data
        // Therefore, we check result after write is done
        for (uint32_t i=0; i<num_words; i++) {
            my_assert(glb[(start_addr>>1)+i], wr_data_array[i], "glb");
        }
    }

private:
    void glb_update() {
        // bank_to_io_rd_data is from glb stub with one cycle latency
        if (m_dut->clk_en != 0) {
            if (io_to_bank_rd_en_d1 == 1) {
                glb_read();
            }
            // due to pipeline registers
            io_to_bank_rd_en_d1 = m_dut->io_to_bank_rd_en;
            io_to_bank_addr_d1 = m_dut->io_to_bank_addr;
        }

        if (m_dut->io_to_bank_wr_en == 1) {
            glb_write();
        }
    }

    void glb_read() {
        m_dut->bank_to_io_rd_data = ((uint64_t) glb[(io_to_bank_addr_d1>>1)+3] << 48)
                                  + ((uint64_t) glb[(io_to_bank_addr_d1>>1)+2] << 32)
                                  + ((uint64_t) glb[(io_to_bank_addr_d1>>1)+1] << 16)
                                  + ((uint64_t) glb[(io_to_bank_addr_d1>>1)+0]);
        printf("Read data from GLB\n");
        printf("\tData: 0x%016lx / Addr: 0x%08x\n", m_dut->bank_to_io_rd_data, io_to_bank_addr_d1);
    }

    void glb_write() {
        glb[((m_dut->io_to_bank_addr>>3)<<2)+0] = (uint16_t) ((m_dut->io_to_bank_wr_data & 0x000000000000FFFF) & (m_dut->io_to_bank_wr_data_bit_sel & 0x000000000000FFFF));
        glb[((m_dut->io_to_bank_addr>>3)<<2)+1] = (uint16_t) (((m_dut->io_to_bank_wr_data & 0x00000000FFFF0000) & (m_dut->io_to_bank_wr_data_bit_sel & 0x00000000FFFF0000)) >> 16);
        glb[((m_dut->io_to_bank_addr>>3)<<2)+2] = (uint16_t) (((m_dut->io_to_bank_wr_data & 0x0000FFFF00000000) & (m_dut->io_to_bank_wr_data_bit_sel & 0x0000FFFF00000000)) >> 32);
        glb[((m_dut->io_to_bank_addr>>3)<<2)+3] = (uint16_t) (((m_dut->io_to_bank_wr_data & 0xFFFF000000000000) & (m_dut->io_to_bank_wr_data_bit_sel & 0xFFFF000000000000)) >> 48);
        printf("Write data to GLB\n");
        printf("\tData: 0x%016lx / Bit_sel: 0x%016lx, Addr: 0x%08x\n", m_dut->io_to_bank_wr_data, m_dut->io_to_bank_wr_data_bit_sel, m_dut->io_to_bank_addr);
    }

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

    // INSTREAM mode testing
    printf("\n");
    printf("/////////////////////////////////////////////\n");
    printf("Start INSTREAM mode test\n");
    printf("/////////////////////////////////////////////\n");
    addr_gen->instream_test(110, 402);
    printf("/////////////////////////////////////////////\n");
    printf("INSTREAM mode is successful\n");
    printf("/////////////////////////////////////////////\n");
    printf("\n");

    // OUTSTREAM mode testing
    printf("\n");
    printf("/////////////////////////////////////////////\n");
    printf("Start OUTSTREAM (sequential) mode test\n");
    printf("/////////////////////////////////////////////\n");
    addr_gen->outstream_test(10, 2);
    printf("/////////////////////////////////////////////\n");
    printf("OUTSTREAM (sequential) mode is successful\n");
    printf("/////////////////////////////////////////////\n");
    printf("\n");

    // OUTSTREAM mode testing
    printf("\n");
    printf("/////////////////////////////////////////////\n");
    printf("Start OUTSTREAM (sequential) mode test\n");
    printf("/////////////////////////////////////////////\n");
    addr_gen->outstream_test(12, 406);
    printf("/////////////////////////////////////////////\n");
    printf("OUTSTREAM (sequential) mode is successful\n");
    printf("/////////////////////////////////////////////\n");
    printf("\n");

    printf("\nAll simulations are passed!\n");
    delete[] glb;
    exit(rcode);
}

