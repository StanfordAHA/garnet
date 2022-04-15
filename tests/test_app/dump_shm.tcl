if { $::env(WAVEFORM) != "0" } {
  database -open cgra -shm
  probe -create top -depth all -all -memories -functions -tasks -shm -database global_buffer
}

if { $::env(SAIF) == "0" } {
  run
  exit
} else {
  stop -name test_toggle -object top.test.test_toggle
  run
  dumpsaif -ewg -scope top.dut -hierarchy -internal -output run.saif -overwrite
  run
  dumpsaif -end
  run
  exit
}
