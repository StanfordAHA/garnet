/*==============================================================================
** Module: test_cfg_controller.cpp
** Description: Test driver for configuration controller
** Author: Taeyoung Kong
** Change history: 05/16/2019 - Implement first version 
** NOTE:    Word size is 64bit, because bitstream size is 64bit wide.
**          Address should be word-aligned.
**          This does not support unaligned access.
**============================================================================*/

#include "Vcfg_controller.h"
#include "verilated.h"
#include "testbench.h"
#include "time.h"
#include <verilated_vcd_c.h>
#include <vector>
#include <random>
#include <string.h>

// Address is byte addressable
uint16_t NUM_BANKS = 32;
uint16_t NUM_CFG = 8;
uint16_t BANK_ADDR_WIDTH = 17;
uint16_t BANK_DATA_WIDTH = 64;
uint16_t CGRA_DATA_WIDTH = 16;
uint16_t CONFIG_FEATURE_WIDTH = 4;
uint16_t CONFIG_REG_WIDTH = 4;

using namespace std;

uint16_t** glb;

typedef enum REG_ID
{
    ID_START_ADDR      = 0,
    ID_NUM_WORDS       = 1,
    ID_SWITCH_SEL      = 2
} REG_ID;

struct Addr_gen
{
    uint16_t id;
    uint32_t start_addr;
    uint32_t int_addr;
    uint32_t num_words;
    uint32_t int_cnt;
    uint32_t switch_sel;
};

class CFG_CTRL {
public:
    CFG_CTRL(uint16_t num_cfg) {
        addr_gens = new Addr_gen[num_cfg];
        this->num_cfg = num_cfg;
        for (uint16_t i=0; i<num_cfg; i++) {
            addr_gens[i].id = i;
            addr_gens[i].start_addr = 0;
            addr_gens[i].int_addr = 0;
            addr_gens[i].int_cnt = 0;
            addr_gens[i].num_words = 0;
            addr_gens[i].switch_sel = 0;
        }
    }
    ~CFG_CTRL(void) {
        delete[] addr_gens; 
    }

    uint16_t get_num_cfg() {
        return this->num_cfg;
    }

    uint32_t get_start_addr(uint16_t num_cfg) {
        return addr_gens[num_cfg].start_addr;
    }

    uint32_t get_int_addr(uint16_t num_cfg) {
        return addr_gens[num_cfg].int_addr;
    }

    uint32_t get_num_words(uint16_t num_cfg) {
        return addr_gens[num_cfg].num_words;
    }

    uint32_t get_int_cnt(uint16_t num_cfg) {
        return addr_gens[num_cfg].int_cnt;
    }

    uint32_t get_switch_sel(uint16_t num_cfg) {
        return addr_gens[num_cfg].switch_sel;
    }

    Addr_gen& get_addr_gen(uint16_t num_cfg) {
        return addr_gens[num_cfg];
    }

    void set_start_addr(uint16_t num_cfg, uint32_t start_addr) {
        if (start_addr % 8 != 0) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Address is not word aligned" << std::endl;
            exit(EXIT_FAILURE);
        }
        addr_gens[num_cfg].start_addr = start_addr;
    }

    void set_int_addr(uint16_t num_cfg, uint32_t int_addr) {
        if (int_addr % 8 != 0) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Address is not word aligned" << std::endl;
            exit(EXIT_FAILURE);
        }
        addr_gens[num_cfg].int_addr = int_addr;
    }

    void set_num_words(uint16_t num_cfg, uint32_t num_words) {
        addr_gens[num_cfg].num_words = num_words;
    }

    void set_int_cnt(uint16_t num_cfg, uint32_t int_cnt) {
        addr_gens[num_cfg].int_cnt = int_cnt;
    }

    void set_switch_sel(uint16_t num_cfg, uint32_t switch_sel) {
        if (switch_sel >= (1<<(NUM_BANKS/NUM_CFG)) ) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "CFG controller " << num_cfg << "select switch cannot be configed to " << std::hex << "0x" << switch_sel <<  std::endl;
            exit(EXIT_FAILURE);
        }
        addr_gens[num_cfg].switch_sel = switch_sel;
    }

private:
    Addr_gen *addr_gens;
    uint16_t num_cfg;
};

class CFG_CTRL_TB : public TESTBENCH<Vcfg_controller> {
public:
    uint32_t *cfg_to_bank_rd_en_d1;
    uint32_t *cfg_to_bank_rd_addr_d1;

    CFG_CTRL_TB(void) {
        cfg_to_bank_rd_en_d1 = new uint32_t[NUM_BANKS];
        cfg_to_bank_rd_addr_d1 = new uint32_t[NUM_BANKS];
        reset();
    }

    ~CFG_CTRL_TB(void) {}

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

    void config_wr(Addr_gen &addr_gen) {
        uint16_t num_id = addr_gen.id;
        config_wr(num_id, ID_START_ADDR, addr_gen.start_addr);
        config_wr(num_id, ID_NUM_WORDS, addr_gen.num_words);
        config_wr(num_id, ID_SWITCH_SEL, addr_gen.switch_sel);
    }

    void config_wr(uint16_t num_ctrl, REG_ID reg_id, uint32_t data) {
        printf("Configuration for %d\n", num_ctrl);
        if (num_ctrl > NUM_CFG ) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Wrong number of io controller" << std::endl;
            m_trace->close();
            exit(EXIT_FAILURE);
        }
        uint32_t feature_id = num_ctrl;
        uint32_t config_addr = (feature_id << CONFIG_REG_WIDTH) + reg_id;
        uint32_t config_data = data;
        m_dut->config_en = 1;
        m_dut->config_wr = 1;
        m_dut->config_addr = config_addr;
        m_dut->config_wr_data = config_data;
        tick();
        m_dut->config_en = 0;
        m_dut->config_wr = 0;

        // why hurry?
        for (uint32_t t=0; t<10; t++)
            tick();
    }

    void config_rd(Addr_gen &addr_gen) {
        uint16_t num_id = addr_gen.id;
        config_rd(num_id, ID_START_ADDR, addr_gen.start_addr);
        config_rd(num_id, ID_NUM_WORDS, addr_gen.num_words);
        config_rd(num_id, ID_SWITCH_SEL, addr_gen.switch_sel);
    }

    void config_rd(uint16_t num_ctrl, REG_ID reg_id, uint32_t data_expected, uint32_t read_delay=10) {
        uint32_t feature_id = num_ctrl;
        uint32_t config_addr = (feature_id << CONFIG_REG_WIDTH) + reg_id;
        m_dut->config_en = 1;
        m_dut->config_rd = 1;
        m_dut->config_addr = config_addr;
        for (uint32_t t=0; t<read_delay; t++)
            tick();
        m_dut->config_en = 0;
        m_dut->config_rd = 0;
        my_assert(m_dut->config_rd_data, data_expected, "config_rd_data");

        // why hurry?
        for (uint32_t t=0; t<10; t++)
            tick();
    }

    void cfg_ctrl_setup(CFG_CTRL* cfg_ctrl) {
        for(uint16_t i=0; i < cfg_ctrl->get_num_cfg(); i++) {
            cfg_ctrl->set_int_addr(i, cfg_ctrl->get_start_addr(i));
            cfg_ctrl->set_int_cnt(i, cfg_ctrl->get_num_words(i));
        }
    }
    
    void test(CFG_CTRL* cfg_ctrl) {
        // glb setting
        for(uint16_t i=0; i<cfg_ctrl->get_num_cfg(); i++) {
            config_wr(cfg_ctrl->get_addr_gen(i)); 
        }

        // why hurry?
        for (uint32_t t=0; t<100; t++) {
            tick();
        }

        // toggle config_start_pulse
        m_dut->config_start_pulse = 1;
        tick();
        m_dut->config_start_pulse = 0;

        // internal counter and address set to num_words and start_address
        cfg_ctrl_setup(cfg_ctrl);

        // latency of read
        tick();

        printf("CFG Controller starts\n");

        while (m_dut->config_done_pulse != 1) {
            tick();
            instream(cfg_ctrl);
        }

        printf("End feeding bitstream\n");
        
        // why hurry?
        for (uint32_t t=0; t<100; t++) {
            tick();
            for(uint16_t i=0; i<cfg_ctrl->get_num_cfg(); i++) {
                my_assert(m_dut->glb_to_cgra_cfg_wr[i], 0, "glb_to_cgra_cfg_wr");
                my_assert(m_dut->glb_to_cgra_cfg_rd[i], 0, "glb_to_cgra_cfg_rd");
            }
        }
    }
    void jtag_test(uint32_t addr, uint32_t data, bool read=0, uint32_t read_delay=10) {
        // why hurry?
        for (uint32_t t=0; t<100; t++) {
            tick();
        }

        printf("JTAG configuration starts\n");


        m_dut->glc_to_cgra_cfg_addr = addr;
        m_dut->glc_to_cgra_cfg_data = data;
        if (read) {
            m_dut->glc_to_cgra_cfg_rd = 1;
            for (uint32_t t=0; t<read_delay; t++)
                tick();
            m_dut->glc_to_cgra_cfg_rd = 0;
        }
        else {
            m_dut->glc_to_cgra_cfg_wr = 1;
            tick();
            m_dut->glc_to_cgra_cfg_wr = 0;
        }
        for(uint16_t i=0; i < NUM_CFG; i++) {
            my_assert(m_dut->glb_to_cgra_cfg_data[i], data, "glb_to_cgra_cfg_data");
            my_assert(m_dut->glb_to_cgra_cfg_addr[i], addr, "glb_to_cgra_cfg_addr");
            if (read) {
                my_assert(m_dut->glb_to_cgra_cfg_wr[i], 0, "glb_to_cgra_cfg_wr");
                my_assert(m_dut->glb_to_cgra_cfg_rd[i], 1, "glb_to_cgra_cfg_rd");
            }
            else {
                my_assert(m_dut->glb_to_cgra_cfg_wr[i], 1, "glb_to_cgra_cfg_wr");
                my_assert(m_dut->glb_to_cgra_cfg_rd[i], 0, "glb_to_cgra_cfg_rd");
            }
        }


        printf("End JTAG configuration\n");
        
        // why hurry?
        for (uint32_t t=0; t<100; t++) {
            tick();
        }
    }

private:

    void instream(CFG_CTRL* cfg_ctrl) {
        for(uint16_t i=0; i < cfg_ctrl->get_num_cfg(); i++) {
            uint32_t int_cnt = cfg_ctrl->get_int_cnt(i);
            uint32_t int_addr = cfg_ctrl->get_int_addr(i);
            uint32_t switch_sel = cfg_ctrl->get_switch_sel(i);
            if (switch_sel != 0) {
                if (int_cnt > 0) {
                    cfg_ctrl->set_int_addr(i, int_addr + 8);
                    cfg_ctrl->set_int_cnt(i, int_cnt - 1);
                    printf("Address generator number %d is streaming bitstream to CGRA.\n", i);
                    printf("\tBitstream addr: 0x%08x / Bitstream data: 0x%08x / Bitstream write : %01d\n", m_dut->glb_to_cgra_cfg_addr[i], m_dut->glb_to_cgra_cfg_data[i], m_dut->glb_to_cgra_cfg_wr[i]);
                    my_assert((uint16_t) (m_dut->glb_to_cgra_cfg_data[i] & 0x0000FFFF), glb[(uint16_t)(int_addr >> BANK_ADDR_WIDTH)][((int_addr & ((1<<BANK_ADDR_WIDTH)-1))>>1)+0], "glb_to_cgra_cfg_data_low");
                    my_assert((uint16_t) ((m_dut->glb_to_cgra_cfg_data[i] & 0xFFFF0000) >> 16), glb[(uint16_t)(int_addr >> BANK_ADDR_WIDTH)][((int_addr & ((1<<BANK_ADDR_WIDTH)-1))>>1)+1], "glb_to_cgra_cfg_data_high");
                    my_assert((uint16_t) (m_dut->glb_to_cgra_cfg_addr[i] & 0x0000FFFF), glb[(uint16_t)(int_addr >> BANK_ADDR_WIDTH)][((int_addr & ((1<<BANK_ADDR_WIDTH)-1))>>1)+2], "glb_to_cgra_cfg_addr_low");
                    my_assert((uint16_t) ((m_dut->glb_to_cgra_cfg_addr[i] & 0xFFFF0000) >> 16), glb[(uint16_t)(int_addr >> BANK_ADDR_WIDTH)][((int_addr & ((1<<BANK_ADDR_WIDTH)-1))>>1)+3], "glb_to_cgra_cfg_addr_high");
                    my_assert(m_dut->glb_to_cgra_cfg_wr[i], 1, "glb_to_cgra_cfg_wr");
                }
            }
            else {
                if (i == 0) {
                    std::cerr << std::endl;  // end the current line
                    std::cerr << "First address generator should be turned on" << std::endl;
                    exit(EXIT_FAILURE);
                }
                printf("Address generator number %d is streaming bitstream to CGRA.\n", i);
                printf("\tBitstream addr: 0x%08x / Bitstream data: 0x%08x / Bitstream write : %01d\n", m_dut->glb_to_cgra_cfg_addr[i], m_dut->glb_to_cgra_cfg_data[i], m_dut->glb_to_cgra_cfg_wr[i]);
                my_assert(m_dut->glb_to_cgra_cfg_addr[i], m_dut->glb_to_cgra_cfg_addr[i-1], "glb_to_cgra_cfg_addr");
                my_assert(m_dut->glb_to_cgra_cfg_data[i], m_dut->glb_to_cgra_cfg_data[i-1], "glb_to_cgra_cfg_data");
                my_assert(m_dut->glb_to_cgra_cfg_wr[i], m_dut->glb_to_cgra_cfg_wr[i-1], "glb_to_cgra_cfg_wr");
            }
        }
    }

    void glb_update() {
        glb_read();
    }

    void glb_read() {
        for (uint16_t i=0; i<NUM_BANKS; i++) {
            if (cfg_to_bank_rd_en_d1[i] == 1) {
                m_dut->bank_to_cfg_rd_data[i] = ((uint64_t) glb[i][(cfg_to_bank_rd_addr_d1[i]>>1)+3] << 48)
                                             + ((uint64_t) glb[i][(cfg_to_bank_rd_addr_d1[i]>>1)+2] << 32)
                                             + ((uint64_t) glb[i][(cfg_to_bank_rd_addr_d1[i]>>1)+1] << 16)
                                             + ((uint64_t) glb[i][(cfg_to_bank_rd_addr_d1[i]>>1)+0]);

                printf("Read data from bank %d\n", i);
                printf("\tData: 0x%016lx / Addr: 0x%08x\n", m_dut->bank_to_cfg_rd_data[i], cfg_to_bank_rd_addr_d1[i]);
            }
            cfg_to_bank_rd_en_d1[i] = m_dut->cfg_to_bank_rd_en[i];
            cfg_to_bank_rd_addr_d1[i] = m_dut->cfg_to_bank_rd_addr[i];
        }
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
        if (argv_tmp == "BANK_ADDR_WIDTH") {
            BANK_ADDR_WIDTH = stoi(argv[i+1], &pos);
        }
        else if (argv_tmp == "BANK_DATA_WIDTH") {
            BANK_DATA_WIDTH = stoi(argv[i+1], &pos);
        }
        else if (argv_tmp == "CGRA_DATA_WIDTH") {
            CGRA_DATA_WIDTH = stoi(argv[i+1], &pos);
        }
        else if (argv_tmp == "CONFIG_FEATURE_WIDTH") {
            CONFIG_FEATURE_WIDTH = stoi(argv[i+1], &pos);
        }
        else if (argv_tmp == "CONFIG_REG_WIDTH") {
            CONFIG_REG_WIDTH = stoi(argv[i+1], &pos);
        }
        else {
            printf("\nParameter wrong!\n");
            return 0;
        }
    }

    srand (time(NULL));
    // Instantiate address generator testbench
    CFG_CTRL_TB *cfg_ctrl_tb = new CFG_CTRL_TB();
    cfg_ctrl_tb->opentrace("trace_cfg_ctrl.vcd");
    cfg_ctrl_tb->reset();

    // Create global buffer stub using array
    glb = new uint16_t*[NUM_BANKS];

    // initialize glb with random 16bit number 
    for (uint16_t i=0; i<NUM_BANKS; i++) {
        glb[i] = new uint16_t[(1<<(BANK_ADDR_WIDTH-1))];
        for (uint32_t j=0; j<(1<<(BANK_ADDR_WIDTH-1)); j++) {
                //glb[i][j]= (uint16_t)rand();
                glb[i][j]= i;
        }
    }

    //============================================================================//
    // configuration test
    //============================================================================//
    CFG_CTRL *cfg_ctrl = new CFG_CTRL(NUM_CFG);

    for(uint16_t i=0; i<cfg_ctrl->get_num_cfg(); i++) {
        uint32_t tmp_start_addr = rand() << 3;
        uint32_t tmp_num_words = rand();
        uint32_t tmp_switch_sel = rand() % 16;
        cfg_ctrl->set_start_addr(i, tmp_start_addr);
        cfg_ctrl->set_num_words(i, tmp_num_words);
        cfg_ctrl->set_switch_sel(i, tmp_switch_sel);
        cfg_ctrl_tb->config_wr(cfg_ctrl->get_addr_gen(i)); 
        cfg_ctrl_tb->config_rd(cfg_ctrl->get_addr_gen(i)); 
    }

    delete cfg_ctrl;

    for (uint32_t t=0; t<500; t++)
        cfg_ctrl_tb->tick();

    //============================================================================//
    // CFG controller test 1
    // cfg_ctrl[0]: on, cfg_ctrl[4]: on
    //============================================================================//
    cfg_ctrl = new CFG_CTRL(NUM_CFG);
    // Set cfg_ctrl[0]
    cfg_ctrl->set_start_addr(0, (0<<BANK_ADDR_WIDTH) + (1<<(BANK_ADDR_WIDTH-2)));
    cfg_ctrl->set_num_words(0, 10);
    cfg_ctrl->set_switch_sel(0, 0b1111);

    // Set cfg_ctrl[4]
    cfg_ctrl->set_start_addr(4, (16<<BANK_ADDR_WIDTH));
    cfg_ctrl->set_num_words(4, 20);
    cfg_ctrl->set_switch_sel(4, 0b1111);

    printf("\n");
    printf("/////////////////////////////////////////////\n");
    printf("Start CFG controller test 1\n");
    printf("/////////////////////////////////////////////\n");
    cfg_ctrl_tb->test(cfg_ctrl);
    printf("/////////////////////////////////////////////\n");
    printf("CFG controller test 1 is successful\n");
    printf("/////////////////////////////////////////////\n");
    printf("\n");
    delete cfg_ctrl;

    for (uint32_t t=0; t<500; t++)
        cfg_ctrl_tb->tick();

    //============================================================================//
    // CFG controller test 2
    // cfg_ctrl[0]: on, cfg_ctrl[1]: off, cfg_ctrl[2]: on, 
    // cfg_ctrl[3]: off, cfg_ctrl[4]: on, cfg_ctrl[5]: off,
    // cfg_ctrl[6]: on, cfg_ctrl[7]: off
    //============================================================================//
    cfg_ctrl = new CFG_CTRL(NUM_CFG);
    // Set cfg_ctrl[0]
    cfg_ctrl->set_start_addr(0, (0<<BANK_ADDR_WIDTH) + (1<<(BANK_ADDR_WIDTH))-240);
    cfg_ctrl->set_num_words(0, 300);
    cfg_ctrl->set_switch_sel(0, 0b1111);

    // Set cfg_ctrl[2]
    cfg_ctrl->set_start_addr(2, (8<<BANK_ADDR_WIDTH) + (1<<(BANK_ADDR_WIDTH))-160);
    cfg_ctrl->set_num_words(2, 100);
    cfg_ctrl->set_switch_sel(2, 0b1111);

    // Set cfg_ctrl[4]
    cfg_ctrl->set_start_addr(4, (16<<BANK_ADDR_WIDTH) + (1<<(BANK_ADDR_WIDTH))-40);
    cfg_ctrl->set_num_words(4, 80);
    cfg_ctrl->set_switch_sel(4, 0b1111);

    // Set cfg_ctrl[4]
    cfg_ctrl->set_start_addr(6, (24<<BANK_ADDR_WIDTH) + (1<<(BANK_ADDR_WIDTH))-80);
    cfg_ctrl->set_num_words(6, 160);
    cfg_ctrl->set_switch_sel(6, 0b1111);

    printf("\n");
    printf("/////////////////////////////////////////////\n");
    printf("Start CFG controller test 2\n");
    printf("/////////////////////////////////////////////\n");
    cfg_ctrl_tb->test(cfg_ctrl);
    printf("/////////////////////////////////////////////\n");
    printf("CFG controller test 2 is successful\n");
    printf("/////////////////////////////////////////////\n");
    printf("\n");

    delete cfg_ctrl;

    for (uint32_t t=0; t<500; t++)
        cfg_ctrl_tb->tick();

    //============================================================================//
    // CFG controller test 3
    // JTAG configuration test 
    //============================================================================//
    cfg_ctrl = new CFG_CTRL(NUM_CFG);

    printf("\n");
    printf("/////////////////////////////////////////////\n");
    printf("Start CFG controller test 3\n");
    printf("/////////////////////////////////////////////\n");
    cfg_ctrl_tb->jtag_test(1234, 5678);
    cfg_ctrl_tb->jtag_test(1234, 5678, 1);
    printf("/////////////////////////////////////////////\n");
    printf("CFG controller test 3 is successful\n");
    printf("/////////////////////////////////////////////\n");
    printf("\n");
    delete cfg_ctrl;

    for (uint32_t t=0; t<500; t++)
        cfg_ctrl_tb->tick();




    printf("\nAll simulations are passed!\n");
    for (uint16_t i=0; i<NUM_BANKS; i++) {
        delete[] glb[i];
    }
    delete[] glb;
    exit(rcode);
}

