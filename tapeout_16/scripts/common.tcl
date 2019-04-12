# Common helper functions and variables to be used in multiple back-end scripts

proc snap_to_grid {input granularity edge_offset} {
   set new_value [expr (ceil(($input - $edge_offset)/$granularity) * $granularity) + $edge_offset]
   return $new_value
}

set pin_grid 0.56
set cell_row_height 0.576
