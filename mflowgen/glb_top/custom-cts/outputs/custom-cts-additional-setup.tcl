# == get submodule clock pin information ==
# set blocks [get_cells -hier -filter {ref_name =~ glb_tile}]
# set clk_pins [get_pins -of_object $blocks -filter {name =~ clk}]

# == assign clock insertion delay based on the SDC information reported in sub-module signoff node
# foreach_in_collection pin $clk_pins {
#     set_ccopt_property -early -max -pin [get_object_name $pin] insertion_delay 258.6ps
#     set_ccopt_property -late  -max -pin [get_object_name $pin] insertion_delay 283.4ps
#     set_ccopt_property -early -min -pin [get_object_name $pin] insertion_delay 204.0ps
#     set_ccopt_property -late  -min -pin [get_object_name $pin] insertion_delay 224.4ps
# }

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Timing Corner                Skew Group                           ID Target    Min ID    Max ID    Avg ID    Std.Dev. ID    Skew Target Type    Skew Target    Skew    Skew window occupancy
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# delay_typical:setup.early    ideal_clock/constraints_default_c        -        238.1     275.2     258.6         7.2        ignored                  -         37.1              -
# delay_typical:setup.late     ideal_clock/constraints_default_c    none         259.9     295.1     283.4         6.1        auto computed       *21.6          35.2    94.1% {273.0, 294.6}
# delay_best:hold.early        ideal_clock/constraints_default_c        -        184.4     220.6     204.0         7.2        ignored                  -         36.2              -
# delay_best:hold.late         ideal_clock/constraints_default_c        -        206.1     237.8     224.4         6.0        ignored                  -         31.7              -
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------