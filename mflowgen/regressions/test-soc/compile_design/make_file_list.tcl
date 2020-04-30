source $::env(ARM_IP_DIR)/utils/verilog_file_list.tcl

set search_path [list]
set rtl_image [verilog_file_list [lindex $argv 0]]

set fp [open [lindex $argv 1] w+]

foreach inc_dir $search_path {
  puts $fp "+incdir+$inc_dir"
}

foreach rtl_file $rtl_image {
  puts $fp "-v $rtl_file"
}

close $fp
