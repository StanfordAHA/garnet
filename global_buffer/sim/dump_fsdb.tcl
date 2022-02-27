if { $::env(WAVEFORM) == "0" && $::env(SAIF) == "0" } {
    run
    exit
} else {
    stop -change top.test.test_toggle
    run

    if { $::env(WAVEFORM) != "0" } {
        dump -file global_buffer.fsdb -type FSDB
        dump -add top -fsdb_opt +mda+packedmda+struct
    }
    if { $::env(SAIF) != "0" } {
        power -gate_level on mda sv
        power top.dut
        power -enable
    }

    run

    if { $::env(SAIF) != "0" } {
        power -disable
        power -report run.saif 1e-15 top.dut
    }
    if { $::env(WAVEFORM) != "0" } {
        dump -close
    }

    run
    exit
}
