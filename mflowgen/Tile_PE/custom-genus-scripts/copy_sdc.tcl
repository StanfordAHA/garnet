exec mkdir outputs/sdc
exec ln -sf ../../results_syn/syn_out.default.sdc outputs/sdc/default.sdc
# exec ln -sf ../../results_syn/syn_out.FIFO.sdc outputs/sdc/FIFO.sdc
# exec ln -sf ../../results_syn/syn_out.SRAM.sdc outputs/sdc/SRAM.sdc
# just to satisfy assertions
exec ln -sf syn_out.default.sdc results_syn/syn_out._default_constraint_mode_.sdc
