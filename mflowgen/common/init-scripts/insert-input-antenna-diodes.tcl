#=========================================================================
# insert-input-antenna-diodes.tcl 
#=========================================================================
# Adding diode cells to avoid potential antenna violation in hierarchical design
# The diodes are only added to input ports (except clock signal)
# Author : 
# Date   : 

set top_input_pins_except_clk [dbGet -p -v [dbGet -p top.terms.isInput 1].name clk]
set count 0

foreach pin $top_input_pins_except_clk {
  # get the pin property
  set net_name [dbGet $pin.net.name]
  set diode_name "IN_PORT_DIODE_${count}"
  set pin_x [dbGet $pin.pt_x]
  set pin_y [dbGet $pin.pt_y]
  # If it is a vector, the net name will be {net_name[0]}, remove the brackets
  if {[string first "\{" $net_name] != -1} {
    set net_name [string range $net_name 1 end-1]
  }
  # create, place, and connect the diode instance
  addInst -cell $ADK_ANTENNA_CELL -inst $diode_name
  placeInstance $diode_name $pin_x $pin_y -placed
  attachTerm $diode_name $ADK_ANTENNA_CELL_PIN $net_name
  # increment counter
  incr count
}

# the diode cells are placed at the same location as the input ports, which is illegal
# refine it to a legal position near the pin, and set the placement status to fixed
refinePlace
dbSet [dbGet -p top.insts.name "IN_PORT_DIODE_*"].pStatus fixed

