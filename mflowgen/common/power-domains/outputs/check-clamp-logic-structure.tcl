
#------------------------------------------------------------------------
# Check clamping logic structure is maintained
# No buffer is inserted on path to AO clamping logic
# AO clamping logic is maintained

# Diodes can be inserted on the input path to fix antenna violations
# It's acceptable to have diodes on the input since diodes dont have
# static power. These diodes are connected directly to the substrate
# and the fanout ends there. 
# ------------------------------------------------------------------------


# Initialize cell count
set ao_cell_cnt 0
set non_ao_diode_cell_cnt 0
set diode_cell_cnt 0

# Check if the first cell that any net from SB port sees an AO cell (or antenna cell)
# Pattern match on AO22D since sizeOk constraint will allow cells
# of different sizes

foreach_in_collection cell  [all_fanout -from [get_ports *SB*] -levels 1 -only_cells ] {
 set attr [get_attribute [get_cells $cell] ref_name]
 set name [get_attribute [get_cells $cell] name]
 puts "$attr $name"
 if {[regexp  {AO22D} $attr] } {
   set ao_cell_cnt [expr $ao_cell_cnt + 1]
 } elseif {[regexp  {ANTENNA} $attr] } { 
   set diode_cell_cnt [expr $diode_cell_cnt + 1]
 } else {
   set non_ao_diode_cell_cnt [expr $non_ao_diode_cell_cnt + 1]
 }
}

# Check the count of AO cells
puts "\n Non-AO cell count is:  "
puts " $non_ao_diode_cell_cnt"

# Check the count of diode cells
puts " Diode cell count is:  "
puts " $diode_cell_cnt"

# Check count of non-AO non-diode cells
puts " AO cell count is:  "
puts " $ao_cell_cnt \n"

# Display if the clamping logic is maintained
if {[expr $non_ao_diode_cell_cnt > 0]} {
   echo "FAIL: Clamping logic structure" "in the SBs and CBs" "is not maintained"
} else {
   echo "PASS: Clamping logic structure" "in the SBs and CBs" "is maintained"
}
