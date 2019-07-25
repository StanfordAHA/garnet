setMultiCpuUsage -localCpu 8
# Add fillers by stripes
set die_size 4899.96
set die_size_half [expr $die_size / 2]
set num_strips 10
set strip_width [expr $die_size / $num_strips]
set cell_list \
"FILL64BWP16P90 FILL64BWP16P90LVT FILL64BWP16P90ULVT FILL32BWP16P90 FILL32BWP16P90LVT FILL32BWP16P90ULVT FILL16BWP16P90 FILL16BWP16P90LVT FILL16BWP16P90ULVT FILL8BWP16P90 FILL8BWP16P90LVT FILL8BWP16P90ULVT FILL4BWP16P90 FILL4BWP16P90LVT FILL4BWP16P90ULVT FILL3BWP16P90 FILL3BWP16P90LVT FILL3BWP16P90ULVT FILL2BWP16P90 FILL2BWP16P90LVT FILL2BWP16P90ULVT FILL1BWP16P90 FILL1BWP16P90LVT FILL1BWP16P90ULVT DCAP64BWP16P90 DCAP64BWP16P90LVT DCAP64BWP16P90ULVT DCAP32BWP16P90 DCAP32BWP16P90LVT DCAP32BWP16P90ULVT DCAP16BWP16P90 DCAP16BWP16P90LVT DCAP16BWP16P90ULVT DCAP8BWP16P90 DCAP8BWP16P90LVT DCAP8BWP16P90ULVT DCAP4BWP16P90 DCAP4BWP16P90LVT DCAP4BWP16P90ULVT"
setFillerMode -scheme locationFirst \
           -minHole true \
           -fitGap true \
           -keepFixed true \
           -diffCellViol false \
           -core $cell_list \
           -add_fillers_with_drc false

for {set i 0} {$i < $num_strips} {incr i} {
  set left [expr max(0, ($i * $strip_width) - 2)]
  set right [expr min($die_size, ($i + 1) * $strip_width)]
  echo "starting strip $i left: $left right $right"
  addFiller -area [list $left 0 $right $die_size]
  echo "finished strip $i left: $left right $right"
  if {[expr ($i % 2) == 1]} {
    write_db "fill_$i.db"
  }
}
