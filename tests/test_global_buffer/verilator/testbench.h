#ifndef TESTBENCH_H
#define TESTBENCH_H

#include <iostream>
#include <stdio.h>
#include <stdint.h>
#include <verilated_vcd_c.h>

template<class VMODULE> class TESTBENCH {
public:
    unsigned long   m_tickcount;
    VMODULE         *m_dut;
    VerilatedVcdC   *m_trace;

    TESTBENCH(void) {
        m_dut = new VMODULE;
        Verilated::traceEverOn(true);
        m_dut->clk = 0;
        eval();
    }

    virtual ~TESTBENCH(void) {
        closetrace();
        delete m_dut;
        m_dut = NULL;
    }

    virtual void opentrace(const char *vcdname) {
        if (!m_trace) {
            m_trace = new VerilatedVcdC;
            m_dut->trace(m_trace, 99); //Trace 99 levels of hierarchy
            m_trace->open(vcdname);
        }
    }

    virtual void closetrace(void){
        if (m_trace) {
            m_trace->close();
            delete m_trace;
            m_trace = NULL;
        }
    }

    virtual void eval(void) {
        m_dut->eval();
    }

    unsigned long tickcount(void) {
        return m_tickcount;
    }

    virtual void reset(void) {
        m_dut->reset = 1;
        this->tick();
        this->tick();
        this->tick();
        this->tick();
        this->tick();
        m_dut->reset = 0;
#ifdef DEBUG
        printf("Reset\n");
#endif
    }
    
    virtual void tick(void) {
        m_tickcount++;

        // All combinational logic should be settled
        // before we tick the clock
        eval();
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

    void my_assert(
            uint64_t got,
            uint64_t expected,
            const char* port) {
        if (got != expected) {
            std::cerr << std::endl;  // end the current line
            std::cerr << "Got      : 0x" << std::hex << got << std::endl;
            std::cerr << "Expected : 0x" << std::hex << expected << std::endl;
            std::cerr << "Port     : " << port << std::endl;
            m_trace->close();
            exit(EXIT_FAILURE);
        }
    }
};

#endif
