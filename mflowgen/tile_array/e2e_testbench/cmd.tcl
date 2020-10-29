database -shm -default waves
probe -shm Interconnect_tb -depth all -all
dumpsaif -scope Interconnect_tb -hierarchy -internal -output outputs/run.saif -overwrite
run
dumpsaif -end
quit
