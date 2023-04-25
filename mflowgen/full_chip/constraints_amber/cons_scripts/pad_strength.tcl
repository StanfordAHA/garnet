#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: Pad Strength Control Constraints
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 18, 2020
#------------------------------------------------------------------------------

foreach idx [list 0 1 2 3 4 5 6 7] {
  set_false_path -through [get_pins core/OUT_PAD_DS_GRP${idx}]
}

set_case_analysis 1 [get_pins core/OUT_PAD_DS_GRP0[0]]
set_case_analysis 1 [get_pins core/OUT_PAD_DS_GRP0[1]]
set_case_analysis 1 [get_pins core/OUT_PAD_DS_GRP0[2]]
