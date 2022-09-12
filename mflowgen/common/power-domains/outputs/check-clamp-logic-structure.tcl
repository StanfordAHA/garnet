
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

# Ensures that all SB input wires go directly to AO cells for clamping or antenna cells.
# This ensures that if neighboring tiles are off, the signals coming from those tiles
# into this one can be clamped to 0 without passing through other cells and burning power.
# We pattern match on AO22[DX] to allow cells of different sizes and drive strengths.

foreach_in_collection sb_port [get_ports *SB*] {
  foreach_in_collection cell  [all_fanout -from $sb_port -levels 1 -only_cells ] {
    set attr [get_attribute [get_cells $cell] ref_name]
    set name [get_attribute [get_cells $cell] hierarchical_name]
    if {[regexp  {AO22[XD]} $attr]} {
      set ao_cell_cnt [expr $ao_cell_cnt + 1]
    } elseif {[regexp  {ANTENNA} $attr] } { 
      set diode_cell_cnt [expr $diode_cell_cnt + 1]
    } else {
      set port_name [get_attribute $sb_port hierarchical_name]
      set non_ao_diode_cell_cnt [expr $non_ao_diode_cell_cnt + 1]
      puts "Non-AO/diode connection found from $port_name to $attr $name"
    }
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
