exec mkdir outputs/sdc
exec ln -sf ../../results_syn/syn_out.UNIFIED_BUFFER.sdc outputs/sdc/UNIFIED_BUFFER.sdc
exec ln -sf ../../results_syn/syn_out.FIFO.sdc outputs/sdc/FIFO.sdc
exec ln -sf ../../results_syn/syn_out.SRAM.sdc outputs/sdc/SRAM.sdc

# set "strict" sdc to be default sdc, this sdc isn't used in downstream pnr because
# it uses the different modes/scenario sdcs anyway. the "strict" sdc is used
# for synth power estimation
exec ln -sf strict.sdc results_syn/syn_out._default_constraint_mode_.sdc
