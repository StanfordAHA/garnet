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
        glb_update();
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

    void config_wr_sram(uint16_t bank, uint32_t addr, uint64_t data) {
        m_dut->top_config_en_glb = 1;
        m_dut->top_config_wr = 1;
        m_dut->top_config_rd = 0;
        m_dut->top_config_addr = (uint32_t) ((1 << (CONFIG_ADDR_WIDTH-2)) + (addr % (1 << BANK_ADDR_WIDTH)) + (bank << BANK_ADDR_WIDTH));
        m_dut->top_config_wr_data = (uint32_t) (data & 0x00000000FFFFFFFF);
        tick();
        m_dut->top_config_addr = (uint32_t) ((1 << (CONFIG_ADDR_WIDTH-2)) + ((addr + 4) % (1 << BANK_ADDR_WIDTH)) + (bank << BANK_ADDR_WIDTH));
        m_dut->top_config_wr_data = (uint32_t) ((data & 0xFFFFFFFF00000000) >> CONFIG_DATA_WIDTH);
        tick();
        m_dut->top_config_en_glb = 0;
        m_dut->top_config_wr = 0;
        m_dut->top_config_rd = 0;
        m_dut->top_config_addr = 0;
        m_dut->top_config_wr_data = 0;
#ifdef DEBUG
		printf("Configuring SRAM. Bank: %d / Data: 0x%016lx / Addr: 0x%04x\n", bank, data, addr);
#endif
    }

    void config_rd_sram(uint16_t bank, uint32_t addr, vector<vector<uint64_t>> array) {
        m_dut->top_config_en_glb = 1;
        m_dut->top_config_wr = 0;
        m_dut->top_config_rd = 1;
        m_dut->top_config_addr = (uint32_t) ((1 << (CONFIG_ADDR_WIDTH-2)) + (addr % (1 << BANK_ADDR_WIDTH)) + (bank << BANK_ADDR_WIDTH));
        tick();
        my_assert(m_dut->top_config_rd_data, (uint32_t)(array[bank][(addr>>3)] & 0x00000000FFFFFFFF), "top_config_rd_data");
		printf("Config reading SRAM. Bank: %d / Data: 0x%08x / Addr: 0x%04x\n", bank, m_dut->top_config_rd_data, addr);

        m_dut->top_config_addr = (uint32_t) ((1 << (CONFIG_ADDR_WIDTH-2)) + ((addr + 4) % (1 << BANK_ADDR_WIDTH)) + (bank << BANK_ADDR_WIDTH));
        tick();
        m_dut->top_config_en_glb = 0;
        my_assert(m_dut->top_config_rd_data, (uint32_t)((array[bank][(addr>>3)] & 0xFFFFFFFF00000000) >> CONFIG_DATA_WIDTH), "top_config_rd_data");
        m_dut->top_config_wr = 0;
        m_dut->top_config_rd = 0;
        m_dut->top_config_addr = 0;
#ifdef DEBUG
		printf("Config reading SRAM. Bank: %d / Data: 0x%08x / Addr: 0x%04x\n", bank, m_dut->top_config_rd_data, addr + 4);
#endif
    }

private:
    void glb_update() {
        glb_write();
        glb_read();
    }

    void glb_read() {
        if (host_rd_en_d2 == 1) {
            uint32_t bank_d2 = host_rd_addr_d2 >> BANK_ADDR_WIDTH;
            uint32_t bank_addr_d2 = host_rd_addr_d2 % (1 << BANK_ADDR_WIDTH);
            my_assert(m_dut->host_rd_data & 0x000000000000FFFF, glb[bank_d2][(bank_addr_d2>>1)+0], "host_rd_data_0");
            my_assert(m_dut->host_rd_data & 0x00000000FFFF0000, glb[bank_d2][(bank_addr_d2>>1)+1], "host_rd_data_1");
            my_assert(m_dut->host_rd_data & 0x0000FFFF00000000, glb[bank_d2][(bank_addr_d2>>1)+2], "host_rd_data_2");
            my_assert(m_dut->host_rd_data & 0xFFFF000000000000, glb[bank_d2][(bank_addr_d2>>1)+3], "host_rd_data_3");
            printf("Read data from bank %d / Data: 0x%016lx / Addr: 0x%08x\n", bank_d2, m_dut->host_rd_data, bank_addr_d2);
        }
        host_rd_en_d2 = host_rd_en_d1;
        host_rd_addr_d2 = host_rd_addr_d1;
        host_rd_en_d1 = m_dut->host_rd_en;
        host_rd_addr_d1 = m_dut->host_rd_addr;
    }

    void glb_write() {
        if (host_wr_strb_d1 != 0) {
            uint32_t bank_d1 = host_wr_addr_d1 >> BANK_ADDR_WIDTH;
            uint32_t bank_addr_d1 = host_wr_addr_d1 % (1 << BANK_ADDR_WIDTH);
            if (((host_wr_strb_d1 & 0b00000011)>>0) == 0b11)
                glb[bank_d1][(bank_addr_d1>>1)+0] = (uint16_t) (host_wr_data_d1 & 0x000000000000FFFF);
            if (((host_wr_strb_d1 & 0b00001100)>>2) == 0b11)
                glb[bank_d1][(bank_addr_d1>>1)+1] = (uint16_t) (host_wr_data_d1 & 0x00000000FFFF0000);
            if (((host_wr_strb_d1 & 0b00110000)>>4) == 0b11)
                glb[bank_d1][(bank_addr_d1>>1)+2] = (uint16_t) (host_wr_data_d1 & 0x0000FFFF00000000);
            if (((host_wr_strb_d1 & 0b11000000)>>6) == 0b11)
                glb[bank_d1][(bank_addr_d1>>1)+3] = (uint16_t) (host_wr_data_d1 & 0xFFFF000000000000);
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
                //glb[i][j]= (uint16_t)rand();
                glb[i][j]= 0;
        }
    }

    GLB_TB *glb_tb = new GLB_TB();
    glb_tb->opentrace("trace_glb_int.vcd");
    glb_tb->reset();

    //============================================================================//
    // Host write and read
    //============================================================================//
    printf("\n");
    printf("/////////////////////////////////////////////\n");
    printf("Start host test\n");
    printf("/////////////////////////////////////////////\n");
    glb_tb->host_write(0, 1000, 1000000, 0b00000011);
    glb_tb->tick();
    glb_tb->host_read(0, 1000);
    glb_tb->tick();
    glb_tb->tick();
    printf("/////////////////////////////////////////////\n");
    printf("Host test is successful\n");
    printf("/////////////////////////////////////////////\n");
    printf("\n");


    for (uint32_t t=0; t<500; t++)
        glb_tb->tick();

    printf("\nAll simulations are passed!\n");
    exit(rcode);
}

