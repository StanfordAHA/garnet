database -open global_buffer -shm
probe -create top.dut -depth all -all -shm -database global_buffer
run 
exit
