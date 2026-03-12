# ==========================================================================================
# Got this constraints from tile_array
# this is used to set the sink type of pass through clk
# ==========================================================================================
set pe_tiles [get_cells -hier -filter {ref_name =~ Tile_PE}]
foreach_in_collection pe_tile $pe_tiles {
    set clk_pin [get_pins -of_object $pe_tile -filter {name =~ clk}]
    set clk_pin_name [get_object_name $clk_pin]
    set_ccopt_property -pin ${clk_pin_name}              sink_type stop
    set_ccopt_property -pin ${clk_pin_name}_pass_through sink_type stop
}

# ==========================================================================================
# Clock Latency for Global Buffer
# ==========================================================================================
set block [get_cells -hier -filter {ref_name =~ global_buffer}]
set clk_pin [get_pins -of_object $block -filter {name =~ clk}]
set_ccopt_property -max -pin [get_object_name $clk_pin] insertion_delay 1051.1ps
set_ccopt_property -min -pin [get_object_name $clk_pin] insertion_delay 628.8ps
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Timing Corner                Skew Group                           ID Target    Min ID    Max ID    Avg ID    Std.Dev. ID    Skew Target Type    Skew Target    Skew     Skew window occupancy
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# delay_typical:setup.early    ideal_clock/constraints_default_c        -        791.9     1013.3    954.6        14.6        ignored                  -         221.4              -
# delay_typical:setup.late     ideal_clock/constraints_default_c    none         822.9     1051.1    986.9        15.7        auto computed       *21.6          228.2    89.9% {974.8, 996.4}
# delay_best:hold.early        ideal_clock/constraints_default_c        -        628.8      782.6    739.0        13.2        ignored                  -         153.8              -
# delay_best:hold.late         ideal_clock/constraints_default_c        -        644.5      813.7    766.1        13.4        ignored                  -         169.2              -
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ==========================================================================================
# Clock Latency for MatrixUnit
# ==========================================================================================
set block [get_cells -hier -filter {ref_name =~ MatrixUnitWrapper}]
set clk_pin [get_pins -of_object $block -filter {name =~ auto_clock_in_clock}]
set_ccopt_property -max -pin [get_object_name $clk_pin] insertion_delay 1525.1ps
set_ccopt_property -min -pin [get_object_name $clk_pin] insertion_delay 859.1ps
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Timing Corner                Skew Group                           ID Target    Min ID    Max ID    Avg ID    Std.Dev. ID    Skew Target Type    Skew Target    Skew     Skew window occupancy
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# delay_typical:setup.early    ideal_clock/constraints_default_c        -        1062.6    1466.2    1186.2       54.8        ignored                  -         403.6              -
# delay_typical:setup.late     ideal_clock/constraints_default_c    none         1096.7    1525.1    1230.3       58.7        auto computed       *21.6          428.4    29.4% {1228.4, 1250.0}
# delay_best:hold.early        ideal_clock/constraints_default_c        -         859.1    1123.4     921.8       42.2        ignored                  -         264.3              -
# delay_best:hold.late         ideal_clock/constraints_default_c        -         885.0    1162.2     957.1       45.2        ignored                  -         277.2              -
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# ==========================================================================================
# Clock Latency for Tile_IOCoreReadyValid
# ==========================================================================================
set blocks [get_cells -hier -filter {ref_name =~ Tile_IOCoreReadyValid}]
set clk_pins [get_pins -of_object $blocks -filter {name =~ clk}]
foreach_in_collection clk_pin $clk_pins {
    set_ccopt_property -max -pin [get_object_name $clk_pin] insertion_delay 178.9ps
    set_ccopt_property -min -pin [get_object_name $clk_pin] insertion_delay 105.4ps
    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Timing Corner                Skew Group                           ID Target    Min ID    Max ID    Avg ID    Std.Dev. ID    Skew Target Type    Skew Target    Skew    Skew window occupancy
    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # delay_typical:setup.early    ideal_clock/constraints_default_c        -        141.2     163.5     153.6         4.9        ignored                  -         22.3              -
    # delay_typical:setup.late     ideal_clock/constraints_default_c    *175.0       156.3     178.9     170.4         4.4        auto computed       *21.6          22.6    99.6% {156.7, 178.3}
    # delay_best:hold.early        ideal_clock/constraints_default_c        -        105.4     124.7     115.5         4.3        ignored                  -         19.3              -
    # delay_best:hold.late         ideal_clock/constraints_default_c        -        117.2     137.6     129.1         4.0        ignored                  -         20.4              -
    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
}

# ==========================================================================================
# Clock Latency for Tile_PE
# ==========================================================================================
set blocks [get_cells -hier -filter {ref_name =~ Tile_PE}]
set clk_pins [get_pins -of_object $blocks -filter {name =~ clk}]
foreach_in_collection clk_pin $clk_pins {
    set_ccopt_property -max -pin [get_object_name $clk_pin] insertion_delay 257.2ps
    set_ccopt_property -min -pin [get_object_name $clk_pin] insertion_delay 91.8ps
    # ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Timing Corner                Skew Group                           ID Target    Min ID    Max ID    Avg ID    Std.Dev. ID    Skew Target Type    Skew Target    Skew     Skew window occupancy
    # ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # delay_typical:setup.early    ideal_clock/constraints_default_c        -        118.2     225.2     164.9        27.0        ignored                  -         107.0              -
    # delay_typical:setup.late     ideal_clock/constraints_default_c    *175.0       129.6     257.2     190.4        31.5        auto computed       *21.6          127.6    58.3% {158.0, 179.6}
    # delay_best:hold.early        ideal_clock/constraints_default_c        -         91.8     164.8     123.8        19.1        ignored                  -          73.0              -
    # delay_best:hold.late         ideal_clock/constraints_default_c        -        100.7     192.3     143.2        22.2        ignored                  -          91.6              -
    # ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
}

# ==========================================================================================
# Clock Latency for Tile_MemCore
# ==========================================================================================
set blocks [get_cells -hier -filter {ref_name =~ Tile_MemCore}]
set clk_pins [get_pins -of_object $blocks -filter {name =~ clk}]
foreach_in_collection clk_pin $clk_pins {
    set_ccopt_property -max -pin [get_object_name $clk_pin] insertion_delay 416.8ps
    set_ccopt_property -min -pin [get_object_name $clk_pin] insertion_delay 137.7ps
    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Timing Corner                Skew Group                                ID Target    Min ID    Max ID    Avg ID    Std.Dev. ID    Skew Target Type    Skew Target    Skew     Skew window occupancy
    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # delay_typical:setup.early    ideal_clock/constraints_FIFO                  -        179.6     268.1     199.9        10.2        ignored                  -          88.5              -
    #                              ideal_clock/constraints_SRAM                  -        187.4     208.7     197.5         4.6        ignored                  -          21.3              -
    #                              ideal_clock/constraints_UNIFIED_BUFFER        -        187.4     370.1     227.4        41.4        ignored                  -         182.7              -
    # delay_typical:setup.late     ideal_clock/constraints_FIFO              none         196.8     314.4     225.2        11.9        auto computed       *21.8          117.6    91.4% {209.5, 231.3}
    #                              ideal_clock/constraints_SRAM              none         207.7     232.3     222.4         5.2        auto computed       *21.4           24.6    98.8% {210.5, 231.9}
    #                              ideal_clock/constraints_UNIFIED_BUFFER    none         207.7     416.8     256.1        47.3        auto computed       *21.4          209.1    60.6% {210.6, 232.0}
    # delay_best:hold.early        ideal_clock/constraints_FIFO                  -        137.7     196.8     153.9         8.8        ignored                  -          59.1              -
    #                              ideal_clock/constraints_SRAM                  -        137.7     162.3     151.1         6.6        ignored                  -          24.6              -
    #                              ideal_clock/constraints_UNIFIED_BUFFER        -        137.7     269.6     171.6        28.9        ignored                  -         131.9              -
    # delay_best:hold.late         ideal_clock/constraints_FIFO                  -        152.9     230.2     174.0        10.0        ignored                  -          77.3              -
    #                              ideal_clock/constraints_SRAM                  -        152.9     181.7     170.9         7.4        ignored                  -          28.8              -
    #                              ideal_clock/constraints_UNIFIED_BUFFER        -        152.9     306.2     194.4        33.4        ignored                  -         153.3              -
    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
}

# proc adk_add_tracks {} {
#     puts "Info: Setting up technology specific routing track width & pitch"
#     add_tracks -width_pitch_pattern {\
#         {m1 offset 0.0 width 0.068 pitch 0.108} \
#         {m2 offset 0.0 width 0.044 pitch 0.090} \
#         {m3 offset 0.0 width 0.044 pitch 0.090} \
#         {m4 offset 0.0 width 0.044 pitch 0.090} \
#         {m5 offset 0.0 width 0.044 pitch 0.090} \
#         {m6 offset 0.0 width 0.044 pitch 0.090} \
#         {m7 offset 0.0 width 0.180 pitch 0.360} \
#         {m8 offset 0.0 width 0.180 pitch 0.360} \
#     }
#     add_tracks -pitch_pattern {m6 offset 0.0 pitch 0.090} -mode replace
# }
# set ADK_CLK_TREE_NDR_NAME           "ndr_wideW_m3_m8"
# set ADK_CLK_TREE_NDR_LAYER_TOP      8
# set ADK_CLK_TREE_NDR_LAYER_BOTTOM   3
# set ADK_CLK_TREE_NDR_WIDTH          { \
#                                         m1 0.068 \
#                                         m2 0.044 \
#                                         m3 0.108 \
#                                         m4 0.108 \
#                                         m5 0.108 \
#                                         m6 0.160 \
#                                         m7 0.360 \
#                                         m8 0.360 \
#                                     }


# add_ndr \
#     -name NDR_2W_2S \
#     -width "m3:m8 2" \
#     -spacing_multiplier "m3:m8 2" \
#     -hard_spacing \
#     -generate_via
# #ERROR (NRDB-158) Missing vias from LAYER m2 to LAYER m3 in RULE NDR_2W_2S. Add the missing via or remove all vias from RULE NDR_2W_2S so that NanoRoute can use the vias from the default RULE.

add_ndr \
    -name NDR_2W_2S \
    -width { \
        m3 0.108 \
        m4 0.108 \
        m5 0.108 \
        m6 0.160 \
        m7 0.360 \
        m8 0.360 \
    }

# -shield_net             VSS
# -shield_side            both_side
create_route_type \
    -name                   clock_top_route \
    -top_preferred_layer    m8 \
    -bottom_preferred_layer m7 \
    -non_default_rule       NDR_2W_2S

create_route_type \
    -name                   clock_trunk_route \
    -top_preferred_layer    m6 \
    -bottom_preferred_layer m5 \
    -non_default_rule       NDR_2W_2S

# create_route_type \
#     -name                   clock_leaf_route \
#     -top_preferred_layer    m4 \
#     -bottom_preferred_layer m3 \
#     -non_default_rule       NDR_2W_2S

set_ccopt_property route_type clock_top_route   -net_type top
set_ccopt_property route_type clock_trunk_route -net_type trunk
set_ccopt_property route_type clock_trunk_route  -net_type leaf

# Allen's NDR Rule
#  create_route_type
#     -name                           cts_top \
#     -top_preferred_layer            M8 \
#     -bottom_preferred_layer         M6 \
#     -preferred_routing_layer_effort high \
#     -min_stack_layer                M4 \
#     -route_rule                     CTS_NDR
 
#  create_route_type \
#     -name                           cts_trunk \
#     -top_preferred_layer            M8 \
#     -bottom_preferred_layer         M6 \
#     -preferred_routing_layer_effort high \
#     -min_stack_layer                M4 \
#     -route_rule                     CTS_NDR
 
#  create_route_type \
#     -name                           cts_leaf \
#     -top_preferred_layer            M7 \
#     -bottom_preferred_layer         M5 \
#     -preferred_routing_layer_effort high \
#     -min_stack_layer                M4 \
#     -route_rule                     CTS_NDR

# Skew groups, maybe it's not useful
# set io_tiles [get_cells -hier -filter {ref_name =~ Tile_IOCoreReadyValid}]
# set io_tile_clk_pins [get_pins -of_object $io_tiles -filter {name =~ clk}]
# create_ccopt_skew_group \
#     -name io_tiles_skew_group \
#     -shared_sinks [get_property $io_tile_clk_pins full_name]

# set cgra_tiles [get_cells -hier Tile_X*_Y01]
# set cgra_tile_clk_pins [get_pins -of_object $cgra_tiles -filter {name =~ clk}]
# create_ccopt_skew_group \
#     -name cgra_tiles_skew_group \
#     -shared_sinks [get_property $cgra_tile_clk_pins full_name]
