exec mkdir outputs/sdc
exec ln -sf ../../results_syn/syn_out.default_c.sdc outputs/sdc/default_c.sdc
# exec ln -sf ../../results_syn/syn_out.FIFO.sdc outputs/sdc/FIFO.sdc
# exec ln -sf ../../results_syn/syn_out.SRAM.sdc outputs/sdc/SRAM.sdc
# just to satisfy assertions
exec ln -sf syn_out.default_c.sdc results_syn/syn_out._default_constraint_mode_.sdc
