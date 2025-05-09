if { $::env(WAVEFORM) != "0" } {
  dump -file global_buffer_mu.fsdb -type FSDB
  dump -add top -fsdb_opt +mda+packedmda+struct
} 

if { $::env(SAIF) == "0" } {
  run
  exit
} else {
  stop -change top.test.test_toggle

  run
  power -gate_level on mda sv
  power top.dut
  power -enable
  run
  power -disable
  power -report run.saif 1e-15 top.dut
  run
  exit
}
