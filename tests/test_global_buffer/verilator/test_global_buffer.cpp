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
#include <random>
#include <string.h>
#include <vector>

#define DEBUG

// Address is byte addressable
uint16_t NUM_BANKS = 32;
uint16_t NUM_IO = 8;
uint16_t NUM_CFG = 8;
uint16_t BANK_ADDR_WIDTH = 17;
uint16_t BANK_DATA_WIDTH = 64;
uint16_t CGRA_DATA_WIDTH = 16;
uint16_t CONFIG_TILE_WIDTH = 2;
uint16_t CONFIG_FEATURE_WIDTH = 4;
uint16_t CONFIG_REG_WIDTH = 4;
uint16_t CFG_ADDR_WIDTH = 32;
uint16_t CFG_DATA_WIDTH = 32;

using namespace std;

uint16_t** glb;

typedef enum TILE
{
    TILE_IO     = 1,
    TILE_CFG    = 2
} TILE;

typedef uint16_t FEATURE;

typedef enum REG
{
    IO_REG_MODE             = 0,
    IO_REG_START_ADDR       = 1,
    IO_REG_NUM_WORDS        = 2,
    IO_REG_SWITCH_SEL       = 3,
    IO_REG_DONE_DELAY       = 4,
    CFG_REG_START_ADDR      = 0,
    CFG_REG_NUM_WORDS       = 1,
    CFG_REG_SWITCH_SEL      = 2
} REG;

typedef enum MODE
{
    IDLE        = 0,
    INSTREAM    = 1,
    OUTSTREAM   = 2,
    SRAM        = 3
} MODE;


class Addr_gen {
public:
    uint16_t id;
    uint32_t start_addr;
    uint32_t int_addr;
    uint32_t num_words;
    uint32_t int_cnt;
    uint32_t switch_sel;

    Addr_gen(uint32_t id) {
        this->id = id;
        start_addr = 0;
        int_addr = 0;
        int_cnt = 0;
        num_words = 0;
        switch_sel = 0;
    }
    virtual ~Addr_gen() {}
};

class IO_addr_gen: public Addr_gen {
public:
    MODE mode;
    uint32_t done_delay;

    IO_addr_gen(uint32_t id) : Addr_gen(id) {
        mode = IDLE;
        done_delay = 0;
    }
    ~IO_addr_gen() {}
};

class Cfg_addr_gen: public Addr_gen {
public:
    Cfg_addr_gen(uint32_t id): Addr_gen(id) {
    }
    ~Cfg_addr_gen() {}
};

class CFG_CTRL {
public:
    CFG_CTRL(uint16_t num_cfg) {
        addr_gens = new Cfg_addr_gen*[num_cfg];
        this->num_cfg = num_cfg;
        for (uint16_t i=0; i<num_cfg; i++) {
            addr_gens[i] = new Cfg_addr_gen(i);
        }
    }
    ~CFG_CTRL(void) {
        for (uint16_t i=0; i<num_cfg; i++)
            delete addr_gens[i]; 
        delete[] addr_gens;
    }

    uint16_t get_num_cfg() {
        return this->num_cfg;
    }

    uint32_t get_start_addr(uint16_t num_cfg) {
        return addr_gens[num_cfg]->start_addr;
    }

    uint32_t get_int_addr(uint16_t num_cfg) {
        return addr_gens[num_cfg]->int_addr;
    }

    uint32_t get_num_words(uint16_t num_cfg) {
        return addr_gens[num_cfg]->num_words;
    }

    uint32_t get_int_cnt(uint16_t num_cfg) {
        return addr_gens[num_cfg]->int_cnt;
    }

    uint32_t get_switch_sel(uint16_t num_cfg) {
        return addr_gens[num_cfg]->switch_sel;
    }

    Cfg_addr_gen* get_addr_gen(uint16_t num_cfg) {
        return addr_gens[num_cfg];
    }

    void set_start_addr(uint16_t num_cfg, uint32_t start_addr) {
        if (start_addr % 8 != 0) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Address is not word aligned" << std::endl;
            exit(EXIT_FAILURE);
        }
        addr_gens[num_cfg]->start_addr = start_addr;
    }

    void set_int_addr(uint16_t num_cfg, uint32_t int_addr) {
        if (int_addr % 8 != 0) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Address is not word aligned" << std::endl;
            exit(EXIT_FAILURE);
        }
        addr_gens[num_cfg]->int_addr = int_addr;
    }

    void set_num_words(uint16_t num_cfg, uint32_t num_words) {
        addr_gens[num_cfg]->num_words = num_words;
    }

    void set_int_cnt(uint16_t num_cfg, uint32_t int_cnt) {
        addr_gens[num_cfg]->int_cnt = int_cnt;
    }

    void set_switch_sel(uint16_t num_cfg, uint32_t switch_sel) {
        if (switch_sel >= (1<<(NUM_BANKS/NUM_CFG)) ) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "CFG controller " << num_cfg << "select switch cannot be configed to " << std::hex << "0x" << switch_sel <<  std::endl;
            exit(EXIT_FAILURE);
        }
        addr_gens[num_cfg]->switch_sel = switch_sel;
    }

private:
    Cfg_addr_gen **addr_gens;
    uint16_t num_cfg;
};

class IO_CTRL {
public:
    IO_CTRL(uint16_t num_io) {
        addr_gens = new IO_addr_gen*[num_io];
        this->num_io = num_io;
        for (uint16_t i=0; i<num_io; i++) {
            addr_gens[i] = new IO_addr_gen(i);
        }
    }
    ~IO_CTRL(void) {
        for (uint16_t i=0; i<num_io; i++)
            delete addr_gens[i]; 
        delete[] addr_gens;
    }

    uint16_t get_num_io() {
        return this->num_io;
    }
    MODE get_mode(uint16_t num_io) {
        return addr_gens[num_io]->mode;
    }
    uint32_t get_start_addr(uint16_t num_io) {
        return addr_gens[num_io]->start_addr;
    }
    uint32_t get_int_addr(uint16_t num_io) {
        return addr_gens[num_io]->int_addr;
    }
    uint32_t get_num_words(uint16_t num_io) {
        return addr_gens[num_io]->num_words;
    }
    uint32_t get_int_cnt(uint16_t num_io) {
        return addr_gens[num_io]->int_cnt;
    }
    uint32_t get_switch_sel(uint16_t num_cfg) {
        return addr_gens[num_cfg]->switch_sel;
    }
    IO_addr_gen* get_addr_gen(uint16_t num_io) {
        return addr_gens[num_io];
    }

    void set_mode(uint16_t num_io, MODE mode) {
        addr_gens[num_io]->mode = mode;
    }
    void set_start_addr(uint16_t num_io, uint32_t start_addr) {
        if (start_addr % 2 != 0) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Address is not word aligned" << std::endl;
            exit(EXIT_FAILURE);
        }
        addr_gens[num_io]->start_addr = start_addr;
    }

    void set_int_addr(uint16_t num_io, uint32_t int_addr) {
        if (int_addr % 2 != 0) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Address is not word aligned" << std::endl;
            exit(EXIT_FAILURE);
        }
        addr_gens[num_io]->int_addr = int_addr;
    }

    void set_num_words(uint16_t num_io, uint32_t num_words) {
        addr_gens[num_io]->num_words = num_words;
    }

    void set_int_cnt(uint16_t num_io, uint32_t int_cnt) {
        addr_gens[num_io]->int_cnt = int_cnt;
    }
    void set_switch_sel(uint16_t num_io, uint32_t switch_sel) {
        if (switch_sel >= (1<<(NUM_BANKS/NUM_IO)) ) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "IO controller " << num_io << "select switch cannot be configed to " << std::hex << "0x" << switch_sel <<  std::endl;
            exit(EXIT_FAILURE);
        }
        addr_gens[num_io]->switch_sel = switch_sel;
    }
private:
    IO_addr_gen **addr_gens;
    uint16_t num_io;
};

class GLB_TB : public TESTBENCH<Vglobal_buffer> {
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

    // TODO: Can make it better
    void glb_config_wr(IO_CTRL* io_ctrl) {
        for (uint16_t i=0; i<io_ctrl->get_num_io(); i++) {
            glb_config_wr(io_ctrl->get_addr_gen(i));
        }
    }
    void glb_config_wr(CFG_CTRL* cfg_ctrl) {
        for (uint16_t i=0; i<cfg_ctrl->get_num_cfg(); i++) {
            glb_config_wr(cfg_ctrl->get_addr_gen(i));
        }
    }

    void glb_config_wr(Addr_gen* addr_gen) {
        TILE tile;
        FEATURE feature;
        REG reg;
        if (dynamic_cast<Cfg_addr_gen*>(addr_gen) != NULL) {
            Cfg_addr_gen *tmp_addr_gen = dynamic_cast<Cfg_addr_gen*>(addr_gen);
            tile = TILE_CFG; 
            glb_config_wr(tile, tmp_addr_gen->id, CFG_REG_START_ADDR, tmp_addr_gen->start_addr);
            glb_config_wr(tile, tmp_addr_gen->id, CFG_REG_NUM_WORDS, tmp_addr_gen->num_words);
            glb_config_wr(tile, tmp_addr_gen->id, CFG_REG_SWITCH_SEL, tmp_addr_gen->switch_sel);
        }
        else if (dynamic_cast<IO_addr_gen*>(addr_gen) != NULL) {
            IO_addr_gen *tmp_addr_gen = dynamic_cast<IO_addr_gen*>(addr_gen);
            tile = TILE_IO; 
            glb_config_wr(tile, tmp_addr_gen->id, IO_REG_MODE, tmp_addr_gen->mode);
            glb_config_wr(tile, tmp_addr_gen->id, IO_REG_START_ADDR, tmp_addr_gen->start_addr);
            glb_config_wr(tile, tmp_addr_gen->id, IO_REG_NUM_WORDS, tmp_addr_gen->num_words);
            glb_config_wr(tile, tmp_addr_gen->id, IO_REG_SWITCH_SEL, tmp_addr_gen->switch_sel);
            glb_config_wr(tile, tmp_addr_gen->id, IO_REG_DONE_DELAY, tmp_addr_gen->done_delay);
        }
        else {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Wrong address generator" << std::endl;
            m_trace->close();
            exit(EXIT_FAILURE);
        }
    }

    void glb_config_wr(TILE tile, FEATURE feature, REG reg, uint32_t data) {
        uint32_t addr = ((tile << (CONFIG_REG_WIDTH+CONFIG_FEATURE_WIDTH))
                      + (feature << (CONFIG_REG_WIDTH))
                      + reg) << 2;
        glb_config_wr(addr, data);
    }

    void glb_config_wr(uint32_t addr, uint32_t data) {
        m_dut->glb_config_wr = 1;
        m_dut->glb_config_addr = addr;
        m_dut->glb_config_wr_data = data;
        tick();
        m_dut->glb_config_wr = 0;
#ifdef DEBUG
		printf("Config global buffer. Data: 0x%08x / Addr: 0x%08x\n", data, addr);
#endif
    }

    // TODO: Can make it better
    void glb_config_rd(IO_CTRL* io_ctrl) {
        for (uint16_t i=0; i<io_ctrl->get_num_io(); i++) {
            glb_config_rd(io_ctrl->get_addr_gen(i));
        }
    }
    void glb_config_rd(CFG_CTRL* cfg_ctrl) {
        for (uint16_t i=0; i<cfg_ctrl->get_num_cfg(); i++) {
            glb_config_rd(cfg_ctrl->get_addr_gen(i));
        }
    }

    void glb_config_rd(Addr_gen* addr_gen) {
        TILE tile;
        FEATURE feature;
        REG reg;
        if (dynamic_cast<Cfg_addr_gen*>(addr_gen) != NULL) {
            Cfg_addr_gen *tmp_addr_gen = dynamic_cast<Cfg_addr_gen*>(addr_gen);
            tile = TILE_CFG; 
            glb_config_rd(tile, tmp_addr_gen->id, CFG_REG_START_ADDR, tmp_addr_gen->start_addr);
            glb_config_rd(tile, tmp_addr_gen->id, CFG_REG_NUM_WORDS, tmp_addr_gen->num_words);
            glb_config_rd(tile, tmp_addr_gen->id, CFG_REG_SWITCH_SEL, tmp_addr_gen->switch_sel);
        }
        else if (dynamic_cast<IO_addr_gen*>(addr_gen) != NULL) {
            IO_addr_gen *tmp_addr_gen = dynamic_cast<IO_addr_gen*>(addr_gen);
            tile = TILE_IO; 
            glb_config_rd(tile, tmp_addr_gen->id, IO_REG_MODE, tmp_addr_gen->mode);
            glb_config_rd(tile, tmp_addr_gen->id, IO_REG_START_ADDR, tmp_addr_gen->start_addr);
            glb_config_rd(tile, tmp_addr_gen->id, IO_REG_NUM_WORDS, tmp_addr_gen->num_words);
            glb_config_rd(tile, tmp_addr_gen->id, IO_REG_SWITCH_SEL, tmp_addr_gen->switch_sel);
            glb_config_rd(tile, tmp_addr_gen->id, IO_REG_DONE_DELAY, tmp_addr_gen->done_delay);
        }
        else {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Wrong address generator" << std::endl;
            m_trace->close();
            exit(EXIT_FAILURE);
        }
    }

    void glb_config_rd(TILE tile, FEATURE feature, REG reg, uint32_t data_expected, uint32_t read_delay=10) {
        uint32_t addr = ((tile << (CONFIG_REG_WIDTH+CONFIG_FEATURE_WIDTH))
                      + (feature << (CONFIG_REG_WIDTH))
                      + reg) << 2;
        m_dut->glb_config_rd = 1;
        m_dut->glb_config_addr = addr;
        for (uint32_t t=0; t<read_delay; t++)
            tick();
        m_dut->glb_config_rd = 0;
        my_assert(m_dut->glb_config_rd_data, data_expected, "config_rd_data");

#ifdef DEBUG
		printf("Config read global buffer. Data: 0x%08x / Addr: 0x%08x\n", m_dut->glb_config_rd_data, addr);
#endif
        // why hurry?
        for (uint32_t t=0; t<10; t++)
            tick();
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

    void io_ctrl_setup(IO_CTRL* io_ctrl) {
        for(uint16_t i=0; i < io_ctrl->get_num_io(); i++) {
            if (io_ctrl->get_mode(i) == OUTSTREAM) {
                printf("Address generator %d : OUTSTREAM\n", i);
                io_ctrl->set_int_addr(i, io_ctrl->get_start_addr(i));
                io_ctrl->set_int_cnt(i, io_ctrl->get_num_words(i));
            }
            else if (io_ctrl->get_mode(i) == INSTREAM) {
                printf("Address generator %d : INSTREAM\n", i);
                io_ctrl->set_int_addr(i, io_ctrl->get_start_addr(i));
                io_ctrl->set_int_cnt(i, io_ctrl->get_num_words(i));
            }
            else if (io_ctrl->get_mode(i) == SRAM)
                printf("Address generator %d : SRAM\n", i);
            else
                printf("Address generator %d : IDLE\n", i);
        }
    }

    void cgra_test(IO_CTRL* io_ctrl, uint32_t latency=10, uint32_t stall_cycle=0) {
        // why hurry?
        for (uint32_t t=0; t<100; t++) {
            tick();
        }

        uint32_t max_num_words = 0;
        for(uint16_t i=0; i < io_ctrl->get_num_io(); i++) {
            if (io_ctrl->get_mode(i) != IDLE) {
                max_num_words = std::max(io_ctrl->get_num_words(i), max_num_words);
            }
        }
        uint16_t* wr_data_array = new uint16_t[max_num_words];
        uint32_t stall_cnt = 0;
        int stall_time = -1;

        // if stall_cycle is non-zero, randomly stall at stall_time to test stall
        if (stall_cycle != 0 && max_num_words > 0) {
            stall_cnt = stall_cycle;
            stall_time = max((rand() % max_num_words)/2, (uint32_t)2);
        }

        for (uint32_t i=0; i<max_num_words; i++)
            //wr_data_array[i] = (uint16_t)rand(); 
            wr_data_array[i] = (uint16_t)i; 

        // toggle cgra_start_pulse
        m_dut->cgra_start_pulse = 1;
        tick();
        m_dut->cgra_start_pulse = 0;

        // internal counter and address set to num_words and start_address
        io_ctrl_setup(io_ctrl);

        // latency of read
        tick();

        // latency of application
        for (uint32_t t=0; t<latency; t++) {
            tick();
            instream(io_ctrl);
        }

        for(uint16_t i=0; i < io_ctrl->get_num_io(); i++) {
            if (io_ctrl->get_mode(i) == OUTSTREAM) {
                m_dut->cgra_to_io_wr_en[i] = 1;
                m_dut->cgra_to_io_wr_data[i] = wr_data_array[0];
            }
        }

        printf("IO Controller starts\n");

        uint32_t num_cnt = 0;
        while (m_dut->cgra_done_pulse != 1) {
            if (num_cnt == stall_time && stall_cnt > 0)  {
                m_dut->glc_to_io_stall = 1;
                stall_cnt--;
            }
            else {
                m_dut->glc_to_io_stall = 0;
            }
            tick();
            instream(io_ctrl);
            outstream(io_ctrl, wr_data_array, num_cnt);
        }
        for (int i = 0; i <= latency; i++) {
            if (num_cnt == stall_time && stall_cnt > 0)  {
                m_dut->glc_to_io_stall = 1;
                stall_cnt--;
            }
            else {
                m_dut->glc_to_io_stall = 0;
            }
            tick();
            instream(io_ctrl);
            outstream(io_ctrl, wr_data_array, num_cnt);
        }

        // check whether data is correctly written to glb
        for(uint16_t i=0; i < io_ctrl->get_num_io(); i++) {
            if (io_ctrl->get_mode(i) == OUTSTREAM) {
                for (uint32_t j=0; j < io_ctrl->get_num_words(i); j++) {
                    // address increase by 2 (byte addressable)
                    uint32_t int_addr = io_ctrl->get_start_addr(i) + 2*j;
                    my_assert(glb[(uint16_t)(int_addr >> BANK_ADDR_WIDTH)][(int_addr & ((1<<BANK_ADDR_WIDTH)-1))>>1], wr_data_array[j], "glb");
                }
            }
        }
        printf("End IO controller\n");
        
        // why hurry?
        for (uint32_t t=0; t<100; t++) {
            tick();
        }
    }

    void cgra_wr_sram(uint16_t num_io, uint16_t wr_en, uint32_t addr, uint32_t data) {
        m_dut->cgra_to_io_wr_en[num_io] = wr_en;
        m_dut->cgra_to_io_wr_data[num_io] = data;
        m_dut->cgra_to_io_addr_high[num_io] = (uint16_t)(addr>>16);
        m_dut->cgra_to_io_addr_low[num_io] = (uint16_t)addr;
        glb[(uint16_t)(addr >> BANK_ADDR_WIDTH)][(addr & ((1<<BANK_ADDR_WIDTH)-1))>>1] = data;
#ifdef DEBUG
        printf("CGRA is writing data to IO controller.\n");
        printf("\tData: 0x%04x / Addr: 0x%08x\n", data, addr);
#endif
    }

    void cgra_rd_sram(uint16_t num_io, uint16_t rd_en, uint32_t addr) {
        m_dut->cgra_to_io_rd_en[num_io] = rd_en;
        m_dut->cgra_to_io_addr_high[num_io] = (uint16_t)(addr>>16);
        m_dut->cgra_to_io_addr_low[num_io] = (uint16_t)addr;
#ifdef DEBUG
        printf("CGRA is reading data from IO controller.\n");
        printf("\tAddr: 0x%08x\n", addr);
#endif
    }

private:
    void instream(IO_CTRL* io_ctrl) {
        for(uint16_t i=0; i < io_ctrl->get_num_io(); i++) {
            if (io_ctrl->get_mode(i) == INSTREAM) {
                uint32_t int_cnt = io_ctrl->get_int_cnt(i);
                uint32_t int_addr = io_ctrl->get_int_addr(i);
                if (int_cnt > 0) {
                    if (m_dut->glc_to_io_stall == 0) {
                        io_ctrl->set_int_addr(i, int_addr + 2);
                        io_ctrl->set_int_cnt(i, int_cnt - 1);
                    }
                    else {
                        int_addr = int_addr - 2;
                    }
#ifdef DEBUG
                    printf("Address generator number %d is streaming data to CGRA.\n", i);
                    printf("\tData: 0x%04x / Addr: 0x%08x / Valid: %01d\n", m_dut->io_to_cgra_rd_data[i], int_addr, m_dut->io_to_cgra_rd_data_valid[i]);
#endif
                    my_assert(m_dut->io_to_cgra_rd_data[i], glb[(uint16_t)(int_addr >> BANK_ADDR_WIDTH)][(int_addr & ((1<<BANK_ADDR_WIDTH)-1))>>1], "io_to_cgra_rd_data");
                    my_assert(m_dut->io_to_cgra_rd_data_valid[i], 1, "io_to_cgra_rd_data_valid");
                }
            }
        }
    }

    void outstream(IO_CTRL* io_ctrl, uint16_t *data_array, uint32_t &num_cnt) {
        // uint16_t next_wr_en = rand() % 2;
        uint16_t next_wr_en = 1;
        for(uint16_t i=0; i < io_ctrl->get_num_io(); i++) {
            if (io_ctrl->get_mode(i) == OUTSTREAM) {
                uint32_t int_addr = io_ctrl->get_int_addr(i);
                uint32_t int_cnt = io_ctrl->get_int_cnt(i);
#ifdef DEBUG
                printf("CGRA is writing data to IO controller.\n");
                printf("\tData: 0x%04x / Addr: 0x%08x / Valid: %01d\n", m_dut->cgra_to_io_wr_data[i], int_addr, m_dut->cgra_to_io_wr_en[i]);
#endif
                if (m_dut->glc_to_io_stall == 0) {
                    if (m_dut->cgra_to_io_wr_en[i] == 1) {
                        glb[(uint16_t)(int_addr >> BANK_ADDR_WIDTH)][(int_addr & ((1<<BANK_ADDR_WIDTH)-1))>>1] = m_dut->cgra_to_io_wr_data[i];
                        io_ctrl->set_int_addr(i, int_addr + 2);
                        io_ctrl->set_int_cnt(i, int_cnt - 1);
                        m_dut->cgra_to_io_wr_data[i] = data_array[++num_cnt];
                    }
                    if (io_ctrl->get_int_cnt(i) == 0)
                        m_dut->cgra_to_io_wr_en[i] = 0;
                    else
                        m_dut->cgra_to_io_wr_en[i] = next_wr_en;
                }
            }
        }
    }

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
#ifdef DEBUG
            printf("Read data from bank %d / Data: 0x%016lx / Addr: 0x%08x\n", bank_d2, m_dut->host_rd_data, bank_addr_d2);
#endif
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
#ifdef DEBUG
            printf("Write data to bank %d / Data: 0x%016lx / Strb: 0x%02x, Addr: 0x%08x\n", bank_d1, host_wr_data_d1, host_wr_strb_d1, host_wr_addr_d1);
#endif
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
    glb_tb->opentrace("trace_global_buffer.vcd");
    glb_tb->reset();
    uint32_t addr_array[30];

    CFG_CTRL *cfg_ctrl = new CFG_CTRL(NUM_CFG);
    IO_CTRL *io_ctrl = new IO_CTRL(NUM_IO);

    //============================================================================//
    // GLB configuration controller configuration
    //============================================================================//
    printf("\n");
    printf("/////////////////////////////////////////////\n");
    printf("Start cfg config test\n");
    printf("/////////////////////////////////////////////\n");

    // Set cfg_ctrl[0]
    cfg_ctrl->set_start_addr(0, (0<<BANK_ADDR_WIDTH) + (1<<(BANK_ADDR_WIDTH-2)));
    cfg_ctrl->set_num_words(0, 10);
    cfg_ctrl->set_switch_sel(0, 0b1111);

    // Set cfg_ctrl[4]
    cfg_ctrl->set_start_addr(4, (16<<BANK_ADDR_WIDTH));
    cfg_ctrl->set_num_words(4, 20);
    cfg_ctrl->set_switch_sel(4, 0b1111);
    
    glb_tb->glb_config_wr(cfg_ctrl);
    glb_tb->glb_config_rd(cfg_ctrl);
    
    // why hurry?
    for (uint32_t t=0; t<100; t++)
        glb_tb->tick();

    delete cfg_ctrl;

    //============================================================================//
    // GLB io controller configuration
    //============================================================================//
    printf("\n");
    printf("/////////////////////////////////////////////\n");
    printf("Start io config test\n");
    printf("/////////////////////////////////////////////\n");

    // Set io_ctrl[0]
    io_ctrl->set_mode(0, INSTREAM);
    io_ctrl->set_start_addr(0, (0<<BANK_ADDR_WIDTH) + (1<<(BANK_ADDR_WIDTH-2))+100);
    io_ctrl->set_num_words(0, 200);
    io_ctrl->set_switch_sel(0, 0b1111);

    // Set io_ctrl[4]
    io_ctrl->set_mode(4, OUTSTREAM);
    io_ctrl->set_start_addr(4, (16<<BANK_ADDR_WIDTH)+100);
    io_ctrl->set_num_words(4, 100);
    io_ctrl->set_switch_sel(4, 0b1111);

    glb_tb->glb_config_wr(io_ctrl);
    glb_tb->glb_config_rd(io_ctrl);
    
    // why hurry?
    for (uint32_t t=0; t<100; t++)
        glb_tb->tick();

    delete io_ctrl;
    
    //============================================================================//
    // SRAM configuration
    //============================================================================//
    printf("\n");
    printf("/////////////////////////////////////////////\n");
    printf("Start SRAM config test\n");
    printf("/////////////////////////////////////////////\n");

    // reset addr_array with random value
    // Config can read/write 32bit at one cycle so word offset is LSB 2bits
    for (uint32_t i=0; i<30; i++) {
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
    for (uint32_t i=0; i<30; i++) {
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
    
    for (uint32_t i=0; i < 1000; i+=8) {
        glb_tb->host_write(0, i, i+1000);
    }

    // why hurry?
    for (uint32_t t=0; t<100; t++)
        glb_tb->tick();

    io_ctrl = new IO_CTRL(NUM_IO);
    // Set io_ctrl[0]
    io_ctrl->set_mode(0, INSTREAM);
    io_ctrl->set_start_addr(0, 0);
    io_ctrl->set_num_words(0, 1000);
    io_ctrl->set_switch_sel(0, 0b1111);

    io_ctrl->set_mode(4, OUTSTREAM);
    io_ctrl->set_start_addr(4, (16<<BANK_ADDR_WIDTH)+100);
    io_ctrl->set_num_words(4, 1000);
    io_ctrl->set_switch_sel(4, 0b1111);

    glb_tb->glb_config_wr(io_ctrl);
    printf("\n");
    printf("/////////////////////////////////////////////\n");
    printf("Start host write / CGRA read test\n");
    printf("/////////////////////////////////////////////\n");
    glb_tb->cgra_test(io_ctrl, 10);
    printf("/////////////////////////////////////////////\n");
    printf("Host write / CGRA read test is successful\n");
    printf("/////////////////////////////////////////////\n");
    printf("\n");

    // why hurry?
    for (uint32_t t=0; t<100; t++)
        glb_tb->tick();

    delete io_ctrl;

    //============================================================================//
    // End
    //============================================================================//

    printf("\nAll simulations are passed!\n");
    exit(rcode);
}

