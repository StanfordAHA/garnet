# == get submodule clock pin information ==
# set blocks [get_cells -hier -filter {ref_name =~ ProcessingElement}]
# set clk_pins [get_pins -of_object $blocks -filter {name =~ clk}]

# == assign clock insertion delay based on the SDC information reported in sub-module signoff node
# foreach_in_collection pin $clk_pins {
#     set_ccopt_property -early -max -pin [get_object_name $pin] insertion_delay 162.1ps
#     set_ccopt_property -late  -max -pin [get_object_name $pin] insertion_delay 177.5ps
#     set_ccopt_property -early -min -pin [get_object_name $pin] insertion_delay 119.5ps
#     set_ccopt_property -late  -min -pin [get_object_name $pin] insertion_delay 131.3ps
# }

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Timing Corner                Skew Group                           ID Target    Min ID    Max ID    Avg ID    Std.Dev. ID    Skew Target Type    Skew Target    Skew    Skew window occupancy
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# delay_typical:setup.early    ideal_clock/constraints_default_c        -        153.3     166.3     162.1         2.9        ignored                  -         13.0              -
# delay_typical:setup.late     ideal_clock/constraints_default_c     175.0       166.0     181.9     177.5         3.4        auto computed        21.6          15.9    100% {166.0, 181.9}
# delay_best:hold.early        ideal_clock/constraints_default_c        -        112.2     123.1     119.5         2.4        ignored                  -         10.9              -
# delay_best:hold.late         ideal_clock/constraints_default_c        -        121.8     135.2     131.3         2.9        ignored                  -         13.4              -
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------