#====================================================================
# genlibdb-constraints.tcl
#====================================================================
# These constraints are passed to Primetime for both the PE and
# memory tiles in order to activate all of the pipeline registers
# in the tile interconnect. This prevents all downstream tools
# from analyzing combinational loops that can be realized
# in the interconnect.
#
# Authors: Alex Carsello, Teguh Hofstee
# Date: 1/24/2020

# These are all the muxes that activate/deactivate the
# interconnect's pipeline registers.
set sb_muxes {RMUX_T0_NORTH_B1 RMUX_T0_SOUTH_B1 RMUX_T0_EAST_B1 RMUX_T0_WEST_B1 RMUX_T1_NORTH_B1 RMUX_T1_SOUTH_B1 RMUX_T1_EAST_B1 RMUX_T1_WEST_B1 RMUX_T2_NORTH_B1 RMUX_T2_SOUTH_B1 RMUX_T2_EAST_B1 RMUX_T2_WEST_B1 RMUX_T3_NORTH_B1 RMUX_T3_SOUTH_B1 RMUX_T3_EAST_B1 RMUX_T3_WEST_B1 RMUX_T4_NORTH_B1 RMUX_T4_SOUTH_B1 RMUX_T4_EAST_B1 RMUX_T4_WEST_B1 RMUX_T0_NORTH_B16 RMUX_T0_SOUTH_B16 RMUX_T0_EAST_B16 RMUX_T0_WEST_B16 RMUX_T1_NORTH_B16 RMUX_T1_SOUTH_B16 RMUX_T1_EAST_B16 RMUX_T1_WEST_B16 RMUX_T2_NORTH_B16 RMUX_T2_SOUTH_B16 RMUX_T2_EAST_B16 RMUX_T2_WEST_B16 RMUX_T3_NORTH_B16 RMUX_T3_SOUTH_B16 RMUX_T3_EAST_B16 RMUX_T3_WEST_B16 RMUX_T4_NORTH_B16 RMUX_T4_SOUTH_B16 RMUX_T4_EAST_B16 RMUX_T4_WEST_B16}

foreach sb_mux $sb_muxes {
    # Get all the config regs that control these muxes
    set config_regs [get_cells -hierarchical [format *%s_sel* $sb_mux] -filter "is_sequential==True"]
    set config_reg_outs [get_pins -of_objects $config_regs -filter "direction==out"]
    # Set config reg values to 1 so that all muxes are activated
    set_case_analysis 1 $config_reg_outs
}

