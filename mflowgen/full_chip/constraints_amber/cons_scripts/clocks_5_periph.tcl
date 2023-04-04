#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: Peripheral Clocks
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 17, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Peripheral Source Clocks (selection using divided clocks from SYSTEM CLOCK)
# ------------------------------------------------------------------------------

foreach idx $clk_div_factors {
  create_generated_clock -name periph_by_${idx}_clk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_sys_fclk/Q] \
      -divide_by ${idx} \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div_from_sysclk/CLK_by_${idx}]
}

# ------------------------------------------------------------------------------
# TIMER0
# ------------------------------------------------------------------------------

foreach idx $clk_div_factors {
  create_generated_clock -name timer0_by_${idx}_clk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div_from_sysclk/CLK_by_${idx}] \
      -divide_by 1 \
      -add \
      -master_clock periph_by_${idx}_clk \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_timer0_clk/CLK_OUT]
}

# Free-running
create_generated_clock -name timer0_fclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_timer0_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock timer0_by_1_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_timer0_fclk/Q]

# Gated
create_generated_clock -name timer0_gclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_timer0_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock timer0_by_1_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_timer0_gclk/Q]


# ------------------------------------------------------------------------------
# TIMER1
# ------------------------------------------------------------------------------

foreach idx $clk_div_factors {
  create_generated_clock -name timer1_by_${idx}_clk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div_from_sysclk/CLK_by_${idx}] \
      -divide_by 1 \
      -add \
      -master_clock periph_by_${idx}_clk \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_timer1_clk/CLK_OUT]
}

# Free-running
create_generated_clock -name timer1_fclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_timer1_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock timer1_by_1_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_timer1_fclk/Q]

# Gated
create_generated_clock -name timer1_gclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_timer1_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock timer1_by_1_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_timer1_gclk/Q]


# ------------------------------------------------------------------------------
# UART0
# ------------------------------------------------------------------------------

foreach idx $clk_div_factors {
  create_generated_clock -name uart0_by_${idx}_clk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div_from_sysclk/CLK_by_${idx}] \
      -divide_by 1 \
      -add \
      -master_clock periph_by_${idx}_clk \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_uart0_clk/CLK_OUT]
}

# Free-running
create_generated_clock -name uart0_fclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_uart0_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock uart0_by_1_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_uart0_fclk/Q]

# Gated
create_generated_clock -name uart0_gclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_uart0_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock uart0_by_1_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_uart0_gclk/Q]

# ------------------------------------------------------------------------------
# UART1
# ------------------------------------------------------------------------------

foreach idx $clk_div_factors {
  create_generated_clock -name uart1_by_${idx}_clk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div_from_sysclk/CLK_by_${idx}] \
      -divide_by 1 \
      -add \
      -master_clock periph_by_${idx}_clk \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_uart1_clk/CLK_OUT]
}

# Free-running
create_generated_clock -name uart1_fclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_uart1_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock uart1_by_1_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_uart1_fclk/Q]

# Gated
create_generated_clock -name uart1_gclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_uart1_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock uart1_by_1_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_uart1_gclk/Q]

# ------------------------------------------------------------------------------
# WDOG
# ------------------------------------------------------------------------------

foreach idx $clk_div_factors {
  create_generated_clock -name wdog_by_${idx}_clk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div_from_sysclk/CLK_by_${idx}] \
      -divide_by 1 \
      -add \
      -master_clock periph_by_${idx}_clk \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_wdog_clk/CLK_OUT]
}

# Free-running
create_generated_clock -name wdog_fclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_wdog_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock wdog_by_1_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_wdog_fclk/Q]

# Gated
create_generated_clock -name wdog_gclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_wdog_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock wdog_by_1_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_wdog_gclk/Q]
