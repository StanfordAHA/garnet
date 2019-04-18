/*==============================================================================
** Module: test_global_buffer.cpp
** Description: Test driver for Global Buffer
** Author: Taeyoung Kong
** Change history: 02/25/2019 - Implement first version of global buffer controller
**                              test driver
**============================================================================*/

#include "Vglobal_buffer.h"
#include "verilated.h"
#include "testbench.h"
#include <verilated_vcd_c.h>
#include <vector>
#include <random>
#include <string.h>

#define MAX_WORD 16

#define DEBUG
#define TEST_HOST_W_HOST_R_BURST
#define TEST_HOST_W_HOST_R_RANDOM
#define TEST_HOST_W_CGRA_R
#define TEST_CGRA_W_HOST_R
#define TEST_CONFIG_W_CONFIG_R
#define TEST_CONFIG_W_CGRA_R

uint16_t NUM_BANKS = 32;
uint16_t BANK_ADDR_WIDTH = 16;
uint16_t BANK_DATA_WIDTH = 64;
uint16_t CONFIG_ADDR_WIDTH = 32;
uint16_t CONFIG_DATA_WIDTH = 32;

using namespace std;

class GLB_TB : public TESTBENCH<Vglobal_buffer> {
public:
    GLB_TB(void) {
        reset();
    }

    ~GLB_TB(void) {}

    void host_write(uint16_t bank, uint16_t addr, uint64_t data_in) {
        m_core->host_wr_en[bank] = 1;
        m_core->host_rd_en[bank] = 0;
        m_core->host_wr_data[bank] = data_in;
        uint16_t int_addr = addr % (1 << BANK_ADDR_WIDTH);
        m_core->host_wr_addr[bank] = int_addr;
        tick();
#ifdef DEBUG
        printf("HOST is writing to bank %d. Data: 0x%016lx / Addr: 0x%04x \n", bank, data_in, addr);
#endif
        m_core->host_wr_en[bank] = 0;
        m_core->host_rd_en[bank] = 0;
    }

    void host_read(uint16_t bank, uint16_t addr, uint64_t data_expected) {
        m_core->host_wr_en[bank] = 0;
        m_core->host_rd_en[bank] = 1;
        uint16_t int_addr = addr % (1 << BANK_ADDR_WIDTH);
        m_core->host_rd_addr[bank] = int_addr;
        tick();
        my_assert(m_core->host_rd_data[bank], data_expected, "host_rd_data");
#ifdef DEBUG
        printf("HOST is reading from bank %d. Data: 0x%016lx / Addr: 0x%04x \n", bank, m_core->host_rd_data[bank], addr);
#endif
        m_core->host_wr_en[bank] = 0;
        m_core->host_rd_en[bank] = 0;
    }

    void cgra_write(uint16_t bank, uint16_t addr, uint64_t data_in) {
        m_core->cgra_wr_en[bank] = 1;
        m_core->cgra_rd_en[bank] = 0;
        m_core->cgra_wr_data[bank] = data_in;
        uint16_t int_addr = addr % (1 << BANK_ADDR_WIDTH);
        m_core->cgra_wr_addr[bank] = int_addr;
        tick();
#ifdef DEBUG
        printf("cgra is writing to bank %d. Data: 0x%016lx / Addr: 0x%04x \n", bank, data_in, addr);
#endif
        m_core->cgra_wr_en[bank] = 0;
        m_core->cgra_rd_en[bank] = 0;
    }

    void cgra_read(uint16_t bank, uint16_t addr, uint64_t data_expected) {
        m_core->cgra_wr_en[bank] = 0;
        m_core->cgra_rd_en[bank] = 1;
        uint16_t int_addr = addr % (1 << BANK_ADDR_WIDTH);
        m_core->cgra_rd_addr[bank] = int_addr;
        tick();
        my_assert(m_core->cgra_rd_data[bank], data_expected, "cgra_rd_data");
#ifdef DEBUG
        printf("cgra is reading from bank %d. Data: 0x%016lx / Addr: 0x%04x \n", bank, m_core->cgra_rd_data[bank], addr);
#endif
        m_core->cgra_wr_en[bank] = 0;
        m_core->cgra_rd_en[bank] = 0;
    }

    void config_wr_sram(uint16_t bank, uint16_t addr, uint64_t data) {
        m_core->top_config_en_glb = 1;
        m_core->top_config_wr = 1;
        m_core->top_config_rd = 0;
        m_core->top_config_addr = (uint32_t) ((1 << (CONFIG_ADDR_WIDTH-2)) + (addr % (1 << BANK_ADDR_WIDTH)) + (bank << BANK_ADDR_WIDTH));
        m_core->top_config_wr_data = (uint32_t) (data & 0x00000000FFFFFFFF);
        tick();
        m_core->top_config_addr = (uint32_t) ((1 << (CONFIG_ADDR_WIDTH-2)) + ((addr + 4) % (1 << BANK_ADDR_WIDTH)) + (bank << BANK_ADDR_WIDTH));
        m_core->top_config_wr_data = (uint32_t) ((data & 0xFFFFFFFF00000000) >> CONFIG_DATA_WIDTH);
        tick();
        m_core->top_config_en_glb = 0;
        m_core->top_config_wr = 0;
        m_core->top_config_rd = 0;
        m_core->top_config_addr = 0;
        m_core->top_config_wr_data = 0;
#ifdef DEBUG
		printf("Configuring SRAM. Bank: %d / Data: 0x%016lx / Addr: 0x%04x\n", bank, data, addr);
#endif
    }

    void config_rd_sram(uint16_t bank, uint16_t addr, uint64_t data_expected) {
        m_core->top_config_en_glb = 1;
        m_core->top_config_wr = 0;
        m_core->top_config_rd = 1;
        m_core->top_config_addr = (uint32_t) ((1 << (CONFIG_ADDR_WIDTH-2)) + (addr % (1 << BANK_ADDR_WIDTH)) + (bank << BANK_ADDR_WIDTH));
        tick();
        my_assert(m_core->top_config_rd_data, (uint32_t)(data_expected & 0x00000000FFFFFFFF), "top_config_rd_data");
		printf("Config reading SRAM. Bank: %d / Data: 0x%08x / Addr: 0x%04x\n", bank, m_core->top_config_rd_data, addr);

        m_core->top_config_addr = (uint32_t) ((1 << (CONFIG_ADDR_WIDTH-2)) + ((addr + 4) % (1 << BANK_ADDR_WIDTH)) + (bank << BANK_ADDR_WIDTH));
        tick();
        m_core->top_config_en_glb = 0;
        my_assert(m_core->top_config_rd_data, (uint32_t)((data_expected & 0xFFFFFFFF00000000) >> CONFIG_DATA_WIDTH), "top_config_rd_data");
        m_core->top_config_wr = 0;
        m_core->top_config_rd = 0;
        m_core->top_config_addr = 0;
#ifdef DEBUG
		printf("Config reading SRAM. Bank: %d / Data: 0x%08x / Addr: 0x%04x\n", bank, m_core->top_config_rd_data, addr + 4);
#endif
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
        else if (argv_tmp == "CONFIG_ADDR_WIDTH") {
            CONFIG_ADDR_WIDTH = stoi(argv[i+1], &pos);
        }
        else if (argv_tmp == "CONFIG_DATA_WIDTH") {
            CONFIG_DATA_WIDTH = stoi(argv[i+1], &pos);
        }
        else {
            printf("\nParameter wrong!\n");
            return 0;
        }
    }

    GLB_TB *glb = new GLB_TB();
    glb->opentrace("trace_glb.vcd");
    glb->reset();

    uint16_t addr = 0;

#ifdef TEST_HOST_W_HOST_R_BURST
    printf("\nTesting HOST write and HOST read in burst mode\n");
    uint64_t data;
    for (uint32_t bank = 0; bank < NUM_BANKS; bank++) {
        addr = 0;
        for (uint32_t j = 0; j < MAX_WORD; j++) {
            mt19937_64 gen(random_device{}());
            data = gen();
            glb->host_write(bank, addr, data);
            glb->host_read(bank, addr, data);
            addr += 8;
        }
        glb->tick();
    }
    printf("\nSUCCESS!\n");
#endif

#ifdef TEST_HOST_W_HOST_R_RANDOM
    printf("\nTesting HOST write and HOST read in random mode\n");
    for (uint32_t bank = 0; bank < NUM_BANKS; bank++) {
        for (uint32_t j = 0; j < MAX_WORD; j++) {
            mt19937_64 gen_data(random_device{}());
            mt19937 gen_addr(random_device{}());
            data = gen_data();
            addr = ((gen_addr() % (1 << BANK_ADDR_WIDTH)) >> 3) << 3;
            glb->host_write(bank, addr, data);
            glb->host_read(bank, addr, data);
        }
        glb->tick();
    }
    printf("\nSUCCESS!\n");
#endif

#ifdef TEST_CONFIG_W_CONFIG_R
    printf("\nTesting config write and config read\n");
    for (uint32_t bank = 0; bank < NUM_BANKS; bank++) {
        addr = 0;
        for (uint16_t j = 0; j < MAX_WORD; j++) {
            mt19937_64 gen(random_device{}());
            data = gen();
            glb->config_wr_sram(bank, addr, data);
            glb->config_rd_sram(bank, addr, data);
            addr += 8;
        }
        glb->tick();
    }
    printf("\nSUCCESS!\n");
#endif

#ifdef TEST_CONFIG_W_CGRA_R
    printf("\nTesting config write and cgra read\n");
    for (uint32_t bank = 0; bank < NUM_BANKS; bank++) {
        addr = 0;
        for (uint16_t j = 0; j < MAX_WORD; j++) {
            mt19937_64 gen(random_device{}());
            data = gen();
            glb->config_wr_sram(bank, addr, data);
            glb->cgra_read(bank, addr, data);
            addr += 8;
        }
        glb->tick();
    }
    printf("\nSUCCESS!\n");
#endif

    glb->tick();
    printf("\nAll simulations are passed!\n");
    exit(rcode);
}

