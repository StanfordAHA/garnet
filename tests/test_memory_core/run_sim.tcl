if { $::env(WAVEFORM) != "0" } {
    database -open -vcd vcddb -into waveforms.vcd -default -timescale ps
    probe -create -all -vcd -depth all
}
run
assertion -summary -final
quit