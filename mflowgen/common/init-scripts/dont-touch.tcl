#=========================================================================
# dont-touch.tcl
#=========================================================================
# Author : Po-Han Chen
# Date   : 2023/11/03
# Usage  : This script is borrowed from the sdc constraint file.
#          Ideally, Genus passes the dont-touch constraint down to Innovus
#          via the output SDC file. However, for some unknown reason, Genus
#          sometimes does NOT include it, which makes Innovus feel it can
#          freely modify the SB Mux select logic. This is bad because we
#          use set_case_analysis to constrain this logic in later stage.
#          The modification Innovus made will mess it up and eventually
#          result in a combinational loop in tile array level.  

# Preserve the RMUXes so that we can easily constrain them later
set rmux_cells [get_cells -hier -regexp .*RMUX_.*_sel_(inst0|value)]
set_dont_touch $rmux_cells true
set_dont_touch_network [get_pins -of_objects $rmux_cells -filter name=~O*]

# TODO: Do we also need to preserve the logic for empty_n and fifo_en?
#       Now it seems fine, but we may need to check it later.
