
# Create a collection of all TSMC memory cells:
set srams [get_cells -hier -regexp -filter {ref_name=~TS[Dd16].*}]

# Create a hash map between names with only _ characters to the actual hierarchy
array unset flat_srams
foreach_in_collection i $srams {
    set flat_srams([string map {/ _} [get_object_name $i]]) $i
}

proc chisel_index {i} {
  if {$i == 0} {
    return ""
  }
  return "_$i"
}

proc phase_index {i} {
  # phase ordering
  set phases {0 1 6 9 12 19}
  return [lindex $phases $i]
}

proc tile_mems {pattern dim_x dim_y anchor_x anchor_y delta_x delta_y {orientation ""}} {
  global flat_srams
  for {set j 0} {$j < $dim_y} {incr j} {
    for {set i 0} {$i < $dim_x} {incr i} {
      if {$orientation == ""} {
        if {[expr $i % 2] == 0} {set ori R0} else {set ori MY}
      } else {
        set ori $orientation
      }
      set pos_x [expr $i * $delta_x + $anchor_x]
      set pos_y [expr $j * $delta_y + $anchor_y]
      # set pattern "*Channel[chisel_index $j]_banks_$i*"
      set matching [lindex [array names flat_srams [subst $pattern]] 0]
      puts "$matching"
      if {[llength $matching] == 0} {
        puts "Error: Pattern $pattern has no matches."
        continue
      } elseif {[llength $matching] != 1} {
        puts "Error: Pattern $pattern is not unique."
        continue
      }
      set mem_inst_name [get_object_name $flat_srams($matching)]
      place_inst $mem_inst_name $pos_x $pos_y $ori -fixed
      create_place_halo -insts $mem_inst_name \
        -halo_deltas {2 2 2 2} -snap_to_site
      create_route_halo -bottom_layer M0 -space 2 -top_layer M3 \
        -inst $mem_inst_name
      array unset $flat_srams($matching)
    }
  }
}

# Rocket memories
# main memory
tile_mems {*Channel[chisel_index $i]_banks_${j}*sram0} 2 4 99.99 656 600 146
tile_mems {*Channel[chisel_index [expr $i+2]]_banks_${j}*sram0} 2 4 99.99 1400 600 146
tile_mems {*Channel[chisel_index [expr $i+4]]_banks_${j}*sram0} 2 4 99.99 2144 600 146
tile_mems {*Channel[chisel_index [expr $i+6]]_banks_${j}*sram0} 2 4 99.99 2888 600 146
# L2
tile_mems {*HellaCacheBank[chisel_index $j]_data_*} 1 4 1800 1300 300 146 MY
tile_mems {*HellaCacheBank[chisel_index $j]_meta*} 1 4 1400 1400 300 108.368
tile_mems {*HellaCacheBank[chisel_index [expr $j+4]]_data_*} 1 4 1800 2100 300 146 MY
tile_mems {*HellaCacheBank[chisel_index [expr $j+4]]_meta*} 1 4 1400 2200 300 108.368
# icache
tile_mems {*ICache_${j}_sram_ICache_0_sram*} 1 4 2500 1700 100 81.344 MY
tile_mems {*tag_array*} 1 1 2500 1602 2 2 MY
# dcache
tile_mems {*data_Data*sram[chisel_index $j]_DataArray*} 1 4 2500 2200 100 89 MY
tile_mems {*Cache_meta_Meta*} 1 1 2500 2556 1 1 MY

# TISAR calibration RAMs
# note the TISAR has M8 stripes that block power/ground access in some places
tile_mems {*adccal_864_[phase_index $i]_*}  6 1 1500 4300 90 35
tile_mems {*adccal_800_[phase_index $i]_*}  6 1 2059 4300 90 35
tile_mems {*adccal_675_[phase_index $i]_*}  6 1 2608 4300 90 35

# FFT memories
tile_mems {*ffastDataSRAM_864_[phase_index [expr ($j+$i*12)/4]]_[expr ($j+$i)%4]_ffast*}  2 12 1500 3609 500 45 
tile_mems {*ffastDataSRAM_800_[phase_index [expr ($j+$i*15)/5]]_[expr ($j+$i)%5]_ffast*}  2 15 2059 3559 500 45 
tile_mems {*ffastDataSRAM_675_[phase_index [expr ($j+$i*15)/5]]_[expr ($j+$i)%5]_ffast*}  2 15 2608 3559 500 45 
tile_mems {*circBuffer_sram_864*} 1 1 1500 3564 120 200
tile_mems {*circBuffer_sram_800*} 1 1 2555 3514 120 200 MY
tile_mems {*circBuffer_sram_688*} 1 1 2608 3514 120 200
# back-end memories, not sure where they should go
tile_mems {*ffastOutBinIdxs*} 1 1 1950 3300 100 100
tile_mems {*ffastOutBinVals*} 1 1 1950 3200 100 100

# Amy's ADC
# Memory numbering and pin order coming out of her ADC don't match much,
# which is why this is all jumbled up
tile_mems {*amyADC_Mem1P_5_rx*}  1 1 2800 2898 100 146
tile_mems {*amyADC_Mem1P_13_rx*} 1 1 2800 2752 100 146
tile_mems {*amyADC_Mem1P_6_rx*}    1 1 2800 2606 100 146
tile_mems {*amyADC_Mem1P_11_rx*}  1 1 2800 2460 100 146
tile_mems {*amyADC_Mem1P_rx*}  1 1 2800 2314 100 146
tile_mems {*amyADC_Mem1P_7_rx*}  1 1 2800 2168 100 146
tile_mems {*amyADC_Mem1P_1_rx*} 1 1 2800 2022 100 146

tile_mems {*amyADC_Mem1P_3_rx*}  1 1 2800 1876 100 146
tile_mems {*amyADC_Mem1P_4_rx*}  1 1 2800 1730 100 146
tile_mems {*amyADC_Mem1P_2_rx*}  1 1 2800 1584 100 146
tile_mems {*amyADC_Mem1P_12_rx*}  1 1 2800 1438 100 146
tile_mems {*amyADC_Mem1P_9_rx*}  1 1 2800 1292 100 146
tile_mems {*amyADC_Mem1P_10_rx*} 1 1 2800 1146 100 146
tile_mems {*amyADC_Mem1P_8_rx*} 1 1 2800 1000 100 146
