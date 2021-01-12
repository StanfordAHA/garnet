exec mkdir outputs/sdc
exec ln -sf ../../results_syn/syn_out.default_c.sdc outputs/sdc/default_c.sdc

# set "strict" sdc to be default sdc, this sdc isn't used in downstream pnr because
# it uses the different modes/scenario sdcs anyway. the "strict" sdc is used
# for synth power estimation
exec ln -sf strict.sdc results_syn/syn_out._default_constraint_mode_.sdc
