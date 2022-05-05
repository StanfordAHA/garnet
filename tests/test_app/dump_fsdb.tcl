
if { $::env(WAVEFORM) != "0" } {
  dump -file cgra.fsdb -type FSDB
  dump -add top -fsdb_opt +mda+packedmda+struct+cell
} elseif { $::env(WAVEFORM_GLB_ONLY) != "0" } {
  dump -file global_buffer.fsdb -type FSDB
  dump -add "top.dut.global_buffer*" -fsdb_opt +mda+packedmda+struct
}

run
exit

