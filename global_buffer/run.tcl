database -open waves -into waves.shm -default
probe -create -all -shm -memories -depth all
run 100000000ns
quit
