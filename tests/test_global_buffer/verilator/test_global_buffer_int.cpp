/*==============================================================================
** Module: test_global_buffer_int.cpp
** Description: Test driver for Global Buffer
** Author: Taeyoung Kong
** Change history: 02/25/2019 - Implement first version of global buffer controller
**                              test driver
**============================================================================*/

#include "Vglobal_buffer_int.h"
#include "verilated.h"
#include "testbench.h"
#include <verilated_vcd_c.h>
#include <vector>
#include <random>
#include <string.h>

#define MAX_WORD 16

#define DEBUG

// Address is byte addressable
uint16_t NUM_BANKS = 32;
uint16_t NUM_IO = 8;
uint16_t BANK_ADDR_WIDTH = 17;
uint16_t BANK_DATA_WIDTH = 64;
uint16_t CGRA_DATA_WIDTH = 16;
uint16_t CONFIG_FEATURE_WIDTH = 8;
uint16_t CONFIG_REG_WIDTH = 8;
uint16_t CFG_ADDR_WIDTH = 32;
uint16_t CFG_DATA_WIDTH = 32;

using namespace std;

uint16_t** glb;

class GLB_TB : public TESTBENCH<Vglobal_buffer_int> {
public:
    uint32_t host_rd_en_d1;
    uint32_t host_rd_addr_d1;
    uint32_t host_rd_en_d2;
    uint32_t host_rd_addr_d2;
    uint32_t host_wr_strb_d1;
    uint32_t host_wr_addr_d1;
    uint64_t host_wr_data_d1;
    GLB_TB(void) {
        host_rd_en_d1 = 0;
        host_rd_addr_d1 = 0;
        host_rd_en_d2 = 0;
        host_rd_addr_d2 = 0;
        host_wr_strb_d1 = 0;
        host_wr_addr_d1 = 0;
        host_wr_data_d1 = 0;
        reset();
    }

    ~GLB_TB(void) {}

    void tick() {
        m_tickcount++;

        // All combinational logic should be settled
        // before we tick the clock
        eval();
        host_update();
        if(m_trace) m_trace->dump(10*m_tickcount-4);

        // Toggle the clock
        // Rising edge
        m_dut->clk = 1;
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

    void host_write(uint16_t bank, uint32_t addr, uint64_t data_in, uint32_t wr_strb=0b11111111) {
        m_dut->host_wr_strb = wr_strb;
        m_dut->host_wr_data = data_in;
        uint32_t int_addr = (bank << BANK_ADDR_WIDTH) + addr % (1 << BANK_ADDR_WIDTH);
        m_dut->host_wr_addr = int_addr;
        tick();
#ifdef DEBUG
        printf("HOST is writing - Bank: %d / Data: 0x%016lx / Addr: 0x%04x / Strobe: 0x%02x\n", bank, data_in, addr, wr_strb);
#endif
        m_dut->host_wr_strb = 0;
    }

    void host_read(uint16_t bank, uint32_t addr) {
        m_dut->host_rd_en = 1;
        uint32_t int_addr = addr % (1 << BANK_ADDR_WIDTH) + (bank << BANK_ADDR_WIDTH);
        m_dut->host_rd_addr = int_addr;
        tick();
#ifdef DEBUG
        printf("HOST is reading from bank %d, addr: 0x%04x.\n", bank, addr);
#endif
        m_dut->host_rd_en = 0;
    }

    void config_sram_wr(uint16_t bank, uint32_t addr, uint32_t data) {
        if (addr % 0b100 != 0) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Address should be aligned to 32bit word size for configuration" << std::endl;
            m_trace->close();
            exit(EXIT_FAILURE);
        }
        m_dut->glb_sram_config_wr = 1;
        m_dut->glb_sram_config_addr = (addr % (1 << BANK_ADDR_WIDTH)) + (bank << BANK_ADDR_WIDTH);
        m_dut->glb_sram_config_wr_data = data;
        tick();
        m_dut->glb_sram_config_wr = 0;
        glb[bank][(addr>>1)+0] = (uint16_t) ((data & 0x0000FFFF) >> 0);
        glb[bank][(addr>>1)+1] = (uint16_t) ((data & 0xFFFF0000) >> 16);
#ifdef DEBUG
		printf("Config writing SRAM. Bank: %d / Data: 0x%08x / Addr: 0x%08x\n", bank, data, addr);
#endif
    }

    void config_sram_rd(uint16_t bank, uint32_t addr, uint32_t read_delay=10) {
        if (addr % 0b100 != 0) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Address should be aligned to 32bit word size for configuration" << std::endl;
            m_trace->close();
            exit(EXIT_FAILURE);
        }
        m_dut->glb_sram_config_rd = 1;
        m_dut->glb_sram_config_addr = (addr % (1 << BANK_ADDR_WIDTH)) + (bank << BANK_ADDR_WIDTH);
        for (uint32_t t=0; t<read_delay; t++)
            tick();
        m_dut->glb_sram_config_rd = 0;
#ifdef DEBUG
		printf("Config reading SRAM. Bank: %d / Data: 0x%08x / Addr: 0x%08x\n", bank, m_dut->glb_sram_config_rd_data, addr);
#endif
        my_assert((uint16_t)((m_dut->glb_sram_config_rd_data & 0x0000FFFF) >> 0), glb[bank][(addr>>1)+0], "config_rd_data_low");
        my_assert((uint16_t)((m_dut->glb_sram_config_rd_data & 0xFFFF0000) >> 16), glb[bank][(addr>>1)+1], "config_rd_data_high");
    }

private:
    void host_update() {
        host_write();
        host_read();
    }

    void host_read() {
        if (host_rd_en_d2 == 1) {
            uint32_t bank_d2 = host_rd_addr_d2 >> BANK_ADDR_WIDTH;
            uint32_t bank_addr_d2 = host_rd_addr_d2 % (1 << BANK_ADDR_WIDTH);
            my_assert((m_dut->host_rd_data & 0x000000000000FFFF)>>0, glb[bank_d2][(bank_addr_d2>>1)+0], "host_rd_data_0");
            my_assert((m_dut->host_rd_data & 0x00000000FFFF0000)>>16, glb[bank_d2][(bank_addr_d2>>1)+1], "host_rd_data_1");
            my_assert((m_dut->host_rd_data & 0x0000FFFF00000000)>>32, glb[bank_d2][(bank_addr_d2>>1)+2], "host_rd_data_2");
            my_assert((m_dut->host_rd_data & 0xFFFF000000000000)>>48, glb[bank_d2][(bank_addr_d2>>1)+3], "host_rd_data_3");
            printf("Read data from bank %d / Data: 0x%016lx / Addr: 0x%08x\n", bank_d2, m_dut->host_rd_data, bank_addr_d2);
        }
        host_rd_en_d2 = host_rd_en_d1;
        host_rd_addr_d2 = host_rd_addr_d1;
        host_rd_en_d1 = m_dut->host_rd_en;
        host_rd_addr_d1 = m_dut->host_rd_addr;
    }

    void host_write() {
        if (host_wr_strb_d1 != 0) {
            uint32_t bank_d1 = host_wr_addr_d1 >> BANK_ADDR_WIDTH;
            uint32_t bank_addr_d1 = host_wr_addr_d1 % (1 << BANK_ADDR_WIDTH);
            if (((host_wr_strb_d1 & 0b00000011)>>0) == 0b11)
                glb[bank_d1][(bank_addr_d1>>1)+0] = (uint16_t) ((host_wr_data_d1 & 0x000000000000FFFF)>>0);
            if (((host_wr_strb_d1 & 0b00001100)>>2) == 0b11)
                glb[bank_d1][(bank_addr_d1>>1)+1] = (uint16_t) ((host_wr_data_d1 & 0x00000000FFFF0000)>>16);
            if (((host_wr_strb_d1 & 0b00110000)>>4) == 0b11)
                glb[bank_d1][(bank_addr_d1>>1)+2] = (uint16_t) ((host_wr_data_d1 & 0x0000FFFF00000000)>>32);
            if (((host_wr_strb_d1 & 0b11000000)>>6) == 0b11)
                glb[bank_d1][(bank_addr_d1>>1)+3] = (uint16_t) ((host_wr_data_d1 & 0xFFFF000000000000)>>48);
            printf("Write data to bank %d / Data: 0x%016lx / Strb: 0x%02x, Addr: 0x%08x\n", bank_d1, host_wr_data_d1, host_wr_strb_d1, host_wr_addr_d1);
        }
        host_wr_strb_d1 = m_dut->host_wr_strb;
        host_wr_addr_d1 = m_dut->host_wr_addr;
        host_wr_data_d1 = m_dut->host_wr_data;
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
        if (argv_tmp == "NUM_BANKS") {
            NUM_BANKS = stoi(argv[i+1], &pos);
        }
        else if (argv_tmp == "BANK_ADDR_WIDTH") {
            BANK_ADDR_WIDTH = stoi(argv[i+1], &pos);
        }
        else if (argv_tmp == "BANK_DATA_WIDTH") {
            BANK_DATA_WIDTH = stoi(argv[i+1], &pos);
        }
        else if (argv_tmp == "CFG_ADDR_WIDTH") {
            CFG_ADDR_WIDTH = stoi(argv[i+1], &pos);
        }
        else if (argv_tmp == "CFG_DATA_WIDTH") {
            CFG_DATA_WIDTH = stoi(argv[i+1], &pos);
        }
        else {
            printf("\nParameter wrong!\n");
            return 0;
        }
    }

    srand (time(NULL));

    // Create global buffer stub using array
    glb = new uint16_t*[NUM_BANKS];

    // initialize glb with 0
    for (uint16_t i=0; i<NUM_BANKS; i++) {
        glb[i] = new uint16_t[(1<<(BANK_ADDR_WIDTH-1))];
        for (uint32_t j=0; j<(1<<(BANK_ADDR_WIDTH-1)); j++) {
                glb[i][j]= 0;
        }
    }

    GLB_TB *glb_tb = new GLB_TB();
    glb_tb->opentrace("trace_glb_int.vcd");
    glb_tb->reset();
    uint32_t addr_array[100];

    //============================================================================//
    // SRAM configuration
    //============================================================================//
    printf("\n");
    printf("/////////////////////////////////////////////\n");
    printf("Start SRAM config test\n");
    printf("/////////////////////////////////////////////\n");

    // reset addr_array with random value
    // Config can read/write 32bit at one cycle so word offset is LSB 2bits
    /*
    for (uint32_t i=0; i<100; i++) {
        addr_array[i] = (((rand() % (1<<BANK_ADDR_WIDTH))>>2)<<2);
    }
    for (uint32_t i=0; i<NUM_BANKS; i++) {
        for (const auto &addr : addr_array) {
            glb_tb->config_sram_wr(i, addr, rand());
        }
    }
    for (uint32_t i=0; i<NUM_BANKS; i++) {
        for (const auto &addr : addr_array) {
            glb_tb->config_sram_rd(i, addr);
        }
    }
    */
    printf("/////////////////////////////////////////////\n");
    printf("SRAM config test is successful\n");
    printf("/////////////////////////////////////////////\n");
    printf("\n");

    // why hurry?
    for (uint32_t t=0; t<100; t++)
        glb_tb->tick();

    //============================================================================//
    // Host write and host read
    //============================================================================//
    // reset addr_array with random value
    // Host can read/write 64bit at one cycle so word offset is LSB 3bits
    for (uint32_t i=0; i<100; i++) {
        addr_array[i] = (((rand() % (1<<BANK_ADDR_WIDTH))>>3)<<3);
    }
    mt19937_64 gen(random_device{}());
    printf("\n");
    printf("/////////////////////////////////////////////\n");
    printf("Start host test\n");
    printf("/////////////////////////////////////////////\n");
    for (uint32_t i=0; i<NUM_BANKS; i++) {
        for (const auto &addr : addr_array) {
            glb_tb->host_write(i, addr, gen());
        }
    }
    for (uint32_t i=0; i<NUM_BANKS; i++) {
        for (const auto &addr : addr_array) {
            glb_tb->host_read(i, addr);
        }
    }
    glb_tb->tick();
    glb_tb->tick();
    printf("/////////////////////////////////////////////\n");
    printf("Host test is successful\n");
    printf("/////////////////////////////////////////////\n");
    printf("\n");

    // why hurry?
    for (uint32_t t=0; t<100; t++)
        glb_tb->tick();

    //============================================================================//
    // Host write and CGRA read
    //============================================================================//
    // why hurry?
    for (uint32_t t=0; t<100; t++)
        glb_tb->tick();

    //============================================================================//
    // CGRA write and host read
    //============================================================================//
    // why hurry?
    for (uint32_t t=0; t<100; t++)
        glb_tb->tick();

    // why hurry?
    for (uint32_t t=0; t<100; t++)
        glb_tb->tick();

    printf("\nAll simulations are passed!\n");
    exit(rcode);
}

