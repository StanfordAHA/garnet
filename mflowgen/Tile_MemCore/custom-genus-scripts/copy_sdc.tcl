exec mkdir outputs/sdc
# exec ln -sf ../../results_syn/syn_out.UNIFIED_BUFFER.sdc outputs/sdc/UNIFIED_BUFFER.sdc
# exec ln -sf ../../results_syn/syn_out.FIFO.sdc outputs/sdc/FIFO.sdc
# exec ln -sf ../../results_syn/syn_out.SRAM.sdc outputs/sdc/SRAM.sdc

# One SDC per constraint mode synthesis created (constraints.tcl: spec
# MemCores have only UNIFIED_BUFFER); custom-flowgen-setup times the modes
# whose SDC is here.
foreach mode {UNIFIED_BUFFER FIFO SRAM} {
  if {[file exists results_syn/syn_out.cstr_mode_${mode}.sdc]} {
    exec ln -sf ../../results_syn/syn_out.cstr_mode_${mode}.sdc outputs/sdc/${mode}.sdc
  }
}

# set "strict" sdc to be default sdc, this sdc isn't used in downstream pnr because
# it uses the different modes/scenario sdcs anyway. the "strict" sdc is used
# for synth power estimation
exec ln -sf strict.sdc results_syn/syn_out._default_constraint_mode_.sdc
