if { $::env(waves) == "True" } {
    database -shm -default waves
    probe -shm $::env(testbench_name) -depth all -all
}

if {[catch {value $::env(testbench_name).saif_window}]} {
    # Legacy tile testbench: the window opens at the stall release, the third
    # stall change (time-0 init, stall 1, stall 0)
    stop -name stall_toggle -object $::env(testbench_name).stall
    run
    run
    run
    stop -delete stall_toggle
} else {
    # App bundle replay: generate_testbench.py raises saif_window when the tile's
    # stall is released, or for a tile the app never stalls (its column is not
    # in use) at the release of the design's other tiles
    # (the condition must reach stop unsubstituted: in a quoted string xmsim
    # replaces #<object> with its current value)
    stop -name app_window -condition [format {#%s.saif_window == 1} $::env(testbench_name)]
    run
    stop -delete app_window
}

dumpsaif -ewg -scope $::env(testbench_name) -hierarchy -internal -output outputs/run.saif -overwrite
if {![catch {value $::env(testbench_name).saif_window_closes}]} {
    # The bundle knows its kernel's length: saif_window falls at the kernel's end, so
    # the SAIF covers the kernel only (not the testbench's output read-back after it);
    # the sim then runs on to $finish, which the replay check needs
    stop -name app_window_end -condition [format {#%s.saif_window == 0} $::env(testbench_name)]
    run
    stop -delete app_window_end
    dumpsaif -end
    run
} else {
    run
    dumpsaif -end
}

quit
