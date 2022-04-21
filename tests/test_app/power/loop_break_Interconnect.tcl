# Loop break constraints
foreach_in_collection tile [get_cells -hier Tile* ] {
  current_instance $tile
  set rmuxes [get_cells -hier *RMUX_*_sel_inst0]
  set rmux_outputs [get_pins -of_objects $rmuxes -filter "direction==out"]
  set_case_analysis 1 $rmux_outputs
  current_instance
}

#set sb_muxes {RMUX_T0_NORTH_B1 RMUX_T0_SOUTH_B1 RMUX_T0_EAST_B1 RMUX_T0_WEST_B1 RMUX_T1_NORTH_B1 RMUX_T1_SOUTH_B1 RMUX_T1_EAST_B1 RMUX_T1_WEST_B1 RMUX_T2_NORTH_B1 RMUX_T2_SOUTH_B1 RMUX_T2_EAST_B1 RMUX_T2_WEST_B1 RMUX_T3_NORTH_B1 RMUX_T3_SOUTH_B1 RMUX_T3_EAST_B1 RMUX_T3_WEST_B1 RMUX_T4_NORTH_B1 RMUX_T4_SOUTH_B1 RMUX_T4_EAST_B1 RMUX_T4_WEST_B1 RMUX_T0_NORTH_B16 RMUX_T0_SOUTH_B16 RMUX_T0_EAST_B16 RMUX_T0_WEST_B16 RMUX_T1_NORTH_B16 RMUX_T1_SOUTH_B16 RMUX_T1_EAST_B16 RMUX_T1_WEST_B16 RMUX_T2_NORTH_B16 RMUX_T2_SOUTH_B16 RMUX_T2_EAST_B16 RMUX_T2_WEST_B16 RMUX_T3_NORTH_B16 RMUX_T3_SOUTH_B16 RMUX_T3_EAST_B16 RMUX_T3_WEST_B16 RMUX_T4_NORTH_B16 RMUX_T4_SOUTH_B16 RMUX_T4_EAST_B16 RMUX_T4_WEST_B16}
#
#foreach sb_mux $sb_muxes {
#    # Get all the config regs that control these muxes
#    set config_regs [get_cells -hierarchical [format *%s_sel* $sb_mux]]
#    set config_reg_outs [get_pins -of_objects $config_regs -filter "direction==out"]
#    # Set config reg values to 1 so that all muxes are activated
#    set_case_analysis 1 $config_reg_outs
#}
