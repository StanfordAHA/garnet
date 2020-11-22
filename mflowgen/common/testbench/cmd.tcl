if { $::env(waves) == "True" } {
    database -shm -default waves
    probe -shm $::env(testbench_name) -depth all -all
}

stop -name stall_toggle -object $::env(testbench_name).stall
run
run
run
stop -delete stall_toggle

dumpsaif -ewg -scope $::env(testbench_name) -hierarchy -internal -output outputs/run.saif -overwrite
run
dumpsaif -end

quit
