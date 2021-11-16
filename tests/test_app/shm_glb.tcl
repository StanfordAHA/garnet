database -open garnet -shm
probe -create top.dut.GlobalBuffer_* -depth all -all -shm -database garnet
probe -create "top.dut.GlobalBuffer_16_32_inst0\$global_buffer_inst0.\glb_tile_gen[0].glb_tile" -depth all -all -shm -database garnet
run 
exit
