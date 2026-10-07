# Xcelium: the testbench $stops at the start and the end of the measurement
# window (after config load + flush release). SAIF covers only that window.
run
dumpsaif -ewg -scope testbench -hierarchy -internal -output run.saif -overwrite
run
dumpsaif -end
run
exit
