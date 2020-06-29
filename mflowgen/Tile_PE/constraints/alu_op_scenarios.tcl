create_scenario Add
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario Sub
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario Adc
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario Sbc
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario Abs
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario GTE_Max
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario LTE_Min
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario Sel
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 1 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario Mult0
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 1 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario Mult1
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 1 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario Mult2
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 1 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario SHR
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 1 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario SHL
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario Or
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario And
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario XOr
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario FP_add
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario FP_sub
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario FP_cmp
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 1 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario FP_mult
source inputs/common.tcl
set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 1 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario FGetMant
source inputs/common.tcl
set_case_analysis 1 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario FAddIExp
source inputs/common.tcl
set_case_analysis 1 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario FSubExp
source inputs/common.tcl
set_case_analysis 1 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario FCnvExp2F
source inputs/common.tcl
set_case_analysis 1 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario FGetFInt
source inputs/common.tcl
set_case_analysis 1 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario FGetFFrac
source inputs/common.tcl
set_case_analysis 1 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

create_scenario FCnvInt2F
source inputs/common.tcl
set_case_analysis 1 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 1 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

set alu_op_scenarios { Add Sub Adc Sbc Abs GTE_Max LTE_Min Sel Mult0 Mult1 Mult2 SHR SHL Or And XOr FP_add FP_sub FP_cmp FP_mult FGetMant FAddIExp FSubExp FCnvExp2F FGetFInt FGetFFrac FCnvInt2F }
