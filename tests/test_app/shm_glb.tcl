database -open garnet -shm
probe -create top.dut.GlobalBuffer_* -depth all -all -shm -database garnet
run 
exit
