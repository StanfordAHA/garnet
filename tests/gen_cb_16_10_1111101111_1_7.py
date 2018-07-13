from connect_box.build_cb_top import define_connect_box, generate_genesis_cb

import os
import mantle as mantle
import magma as m

param_width = 16
param_num_tracks = 10
param_feedthrough_outputs = "1111101111"
param_has_constant = 1
param_default_value = 7

generate_genesis_cb(param_width, param_num_tracks, param_feedthrough_outputs, param_has_constant, param_default_value)

cb = define_connect_box(param_width, param_num_tracks, param_has_constant, param_default_value, param_feedthrough_outputs)
m.compile(cb.name, cb, output='coreir')
os.system('coreir -i ' + cb.name + '.json -o ' + cb.name + '.v')

os.system('./tests/run_sim.sh')


