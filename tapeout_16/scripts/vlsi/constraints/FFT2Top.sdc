#===============================================================================
# Copyright (C) 2016 Northrop Grumman Corporation
#===============================================================================
# PROJECT:     CRAFT_P1
# DESCRIPTION: SDC constraints
# AUTHOR:      Sergio Montano
#===============================================================================


set_time_unit -nanoseconds
set_load_unit -picofarads

#----------------------------------
# Mode Definition: Functional mode;
#----------------------------------


#set_case_analysis 0 [get_port io_clkrxvin ]

#--------------------------
# Clock Definitions;
#--------------------------

# Clock Periods

set CPU_CLK_P 2.0 ; # 500 MHz
# interface clock (serial adapter)
set ITF_CLK_P 10.0 ; # 100 MHz
# serdes scan clock
set SERDESSCAN_CLK_P 10.0 ; # 100 MHz
# serdes TX/RX clocks
set SERDESRX_CLK_P 1.5; # 625 MHz plus margin
set SERDESTX_CLK_P 1.5; # 625 MHz plus margin
# RXADC clock
set RXADC_CLK_P 5; # 150 MHZ

# PRIMARY CLOCKS

# core and serial interface
create_clock -name CLK_CPU -period $CPU_CLK_P [get_pin  FFT2Core/FFT2CoreTop/clkrx/VOBUF]
create_clock -name CLK_ITF -period $ITF_CLK_P [get_pin  FFT2Pads/IOPAD_io_serial_clock*/C]

# serdes
create_clock -name CLK_SERDESSCAN -period $SERDESSCAN_CLK_P [get_pin FFT2Pads/IOPAD_io_serdes_scan_clk*/C]
create_clock -name CLK_SERDESRX -period $SERDESRX_CLK_P [get_pin -hier serdes_afe_dut/rx_digital_clk]
create_clock -name CLK_SERDESTX -period $SERDESTX_CLK_P [get_pin -hier serdes_afe_dut/tx_digital_clk]

# ADCs
create_clock -name CLK_RXADC -period $RXADC_CLK_P [get_pin FFT2Core/FFT2CoreTop/amyADC/amyBlackBox/rx_adc_mem_clk_out]

# Generated Clocks

# clock groups
set_clock_group -name ASYNC -async -group {CLK_CPU} \
                                   -group {CLK_ITF} \
                                   -group {CLK_SERDESSCAN} \
                                   -group {CLK_SERDESRX} \
                                   -group {CLK_SERDESTX} \
                                   -group {CLK_RXADC}

# latency and uncertaincy
if {![info exists POSTCTS]} {
   set_clock_latency 1.0 [get_clock CLK_CPU]
   set_clock_latency 1.0 [get_clock CLK_ITF]

   set_clock_uncertainty 0.1 [all_clocks]
} else {
   set_propagated_clock      [all_clocks]
   set_clock_uncertainty 0.1 [all_clocks]
}




#deserializer may benefit from multi_cycle_path from 1.2GHz clock to 300MHz cloc

#--------------------------
# I/O Constraints
#--------------------------

# [stevo]: no guarantees on these signals, so make them loose to avoid timing issues

# Inputs
set_input_delay [expr 0.1*${ITF_CLK_P}] -clock CLK_ITF [get_port io_serial_in_bits]
set_input_delay [expr 0.1*${ITF_CLK_P}] -clock CLK_ITF [get_port io_serial_in_valid]
set_input_delay [expr 0.1*${ITF_CLK_P}] -clock CLK_ITF [get_port io_serial_out_ready]

set_input_delay [expr 0.1*${SERDESSCAN_CLK_P}] -clock CLK_SERDESSCAN [get_port io_serdes_scan_in]
set_input_delay [expr 0.1*${SERDESSCAN_CLK_P}] -clock CLK_SERDESSCAN [get_port io_serdes_scan_en]

set_input_transition  1.0 [all_inputs]


# Outputs
set_output_delay [expr 0.1*${ITF_CLK_P}] -clock CLK_ITF  [get_port io_serial_out_bits]
set_output_delay [expr 0.1*${ITF_CLK_P}] -clock CLK_ITF  [get_port io_serial_out_valid]
set_output_delay [expr 0.1*${ITF_CLK_P}] -clock CLK_ITF  [get_port io_serial_in_ready]

set_output_delay [expr 0.1*${SERDESSCAN_CLK_P}] -clock CLK_SERDESSCAN  [get_port io_serdes_scan_out]

set_load 2.0 [all_outputs]


#--------------------------
# Path Exceptions;
#--------------------------

set_false_path       -from  [get_port *reset]; #
