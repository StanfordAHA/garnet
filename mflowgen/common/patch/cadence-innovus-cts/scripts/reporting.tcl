#=========================================================================
# reporting.tcl
#=========================================================================
# Author : Christopher Torng
# Date   : March 26, 2018

report_ccopt_clock_trees -list_special_pins -filename $vars(rpt_dir)/$vars(step).clock_trees.rpt
report_ccopt_skew_groups -filename $vars(rpt_dir)/$vars(step).skew_groups.rpt

# v19 does not support the '-expand_generated_clock_trees' arg
# Legacy reporting script does not even do this, so maybe just leave it out altogether for older Innovus
set version [ string range [ getVersion ] 0 1 ]
if {[ expr $version > 19 ]} {
  report_ccopt_clock_tree_structure -show_sinks -expand_generated_clock_trees independently -file $vars(rpt_dir)/$vars(step).structure.rpt
}

