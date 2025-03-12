from enum import Enum

def main():
    # because hwtypes has deprecated/does not have useful functions for extracting
    # ALU op values, I have copied the ALU ops here as a proper Python Enum

    class ALU_t(Enum):
        Add = 0
        Sub = 1
        Adc = 2
        Sbc = 6
        Abs = 3
        GTE_Max = 4
        LTE_Min = 5
        Sel = 8
        Mult0 = 0xb
        Mult1 = 0xc
        Mult2 = 0xd
        SHR = 0xf
        SHL = 0x11
        Or = 0x12
        And = 0x13
        XOr = 0x14
        FP_add = 0x16
        FP_sub = 0x17
        FP_cmp = 0x18
        FP_mult = 0x19
        FGetMant = 0x92
        FAddIExp = 0x93
        FSubExp = 0x94
        FCnvExp2F = 0x95
        FGetFInt = 0x96
        FGetFFrac = 0x97
        FCnvInt2F = 0x98

    report = open('alu_op_scenarios.tcl', 'w')
    false_paths = '''
set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]
'''

    scenarios  = []
    for op in ALU_t:
        scenarios.append(op.name)
        report.write(f'create_mode -name {op.name}\nset_constraint_mode {op.name}\nsource inputs/common.tcl\n')
        binary_str = f'{op.value:08b}'[::-1]
        for i in range(len(binary_str)-1, -1, -1):
            report.write(f'set_case_analysis {binary_str[i]} [get_pins $alu_path/alu[{i}]]\n')
        report.write(false_paths)
        report.write('\n')

    report.write(f'set alu_op_scenarios {{ {" ".join(scenarios)} }}\n')

    report.close()

if __name__ == '__main__':
    main()
