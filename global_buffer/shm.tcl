database -open glb -shm
# Add direct children of glb_top to probe
probe -create top.dut -depth 1 -all -shm -database glb
# Only add the first tile to make run faster
probe -create {top.dut.\glb_tile_gen[0].glb_tile }  -depth all -all -shm -database glb
run 
exit
