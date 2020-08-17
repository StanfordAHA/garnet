exec mkdir outputs/sdc
exec ln -sf ../../results_syn/syn_out.UNIFIED_BUFFER.sdc outputs/sdc/UNIFIED_BUFFER.sdc
exec ln -sf ../../results_syn/syn_out.FIFO.sdc outputs/sdc/FIFO.sdc
exec ln -sf ../../results_syn/syn_out.SRAM.sdc outputs/sdc/SRAM.sdc
# just to satisfy assertions
exec ln -sf syn_out.SRAM.sdc results_syn/syn_out._default_constraint_mode_.sdc
