##### PARAMETERS #####
# tile size/placement grid granularity
# set x grid granularity to LCM of M3 and M5 and finfet pitches 
# (layers where we placed vertical pins)
set tile_x_grid 1.68
# TODO: set pin_x_grid [lcm 0.07 0.08] 
set pin_x_grid 0.56
#set tile_x_grid [lcm $tile_x_grid 0.09]
set tile_x_grid 5.04
# set y grid granularity to LCM of M4 and M6 pitches 
# (layers where we placed horizontal pins) and std_cell row height
set tile_y_grid 2.88
set pin_y_grid 0.08

# PolyPitch grid parameters
set polypitch_x 0.09
set polypitch_y 0.576

# Tile size parameters
set min_tile_height 85
set min_tile_width 65
set Tile_PE_util 0.7
set Tile_MemCore_util 0.7

# Max routing layer parameters
set max_route_layer(Tile_MemCore) 7
set max_route_layer(Tile_PE) 7

# Power stripe parameters
#stripe width
set tile_stripes(M7,width) 1
set tile_stripes(M8,width) 3
set tile_stripes(M9,width) 4
#stripe spacing
set tile_stripes(M7,spacing) 0.5
set tile_stripes(M8,spacing) 2
set tile_stripes(M9,spacing) 2
#stripe set to set distance
if $::env(PWR_AWARE) {
  set tile_stripes(M7,s2s) 10
  set tile_stripes(M8,s2s) 15
  set tile_stripes(M9,s2s) 20
} else {
  set tile_stripes(M7,s2s) 10
  set tile_stripes(M8,s2s) 15
  set tile_stripes(M9,s2s) 20
}
#stripe start
set tile_stripes(M7,start) 2
set tile_stripes(M8,start) 4
set tile_stripes(M9,start) 4
#stripe direction
set tile_stripes(M7,direction) vertical
set tile_stripes(M8,direction) horizontal
set tile_stripes(M9,direction) vertical

##Tile IO widths (TODO: CALCULATE THESE)
set ns_io_width 53
set ew_io_width 22

##### END PARAMETERS #####

set tile_stripes_array [array get tile_stripes]
