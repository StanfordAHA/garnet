import sys
pins = []
with open(sys.argv[1], 'r') as f:
  in_pulse_width = False
  for line in f.readlines():
    if 'pulse_width' in line:
      in_pulse_width = True
    elif 'Check type' in line:
      in_pulse_width = False
    if in_pulse_width:
      if 'FFT2Core' in line:
        pins.append(line.strip().split(' ')[0])

with open('upsize_drivers.tcl', 'w') as f:
  f.write('set_db eco_batch_mode true\n')
  f.write('set drivers ""\n')
  for pin in pins:
    f.write('lappend drivers [get_db [get_db [get_db [get_db [get_db pins %s] .net] .drivers] .inst] .name]\n'%(pin))
  f.write('eco_update_cell -insts $drivers -cell CKND12BWP16P90LVT\n')
  f.write('set_db eco_batch_mode false\n')
  f.write('# [stevo]: redo timing with this, otherwise it still reports old results\n')
  f.write('report_timing -through %s -early\n'%(pins[0]))
  for pin in pins:
    f.write('set_db [get_db [get_db [get_db [get_db pins %s] .net] .drivers] .inst] .dont_touch true\n'%(pin))
