import pytest
import os
import subprocess
import inspect
from bit_vector import BitVector
from testvectors import test_input, test_output

__all__ = ['harness', 'compile']

def to_string(val):
    if isinstance(val, bool) or isinstance(val, BitVector) and val.num_bits == 1:
        return "1" if val else "0"
    else:
        return str(BitVector(val, num_bits=16)._value)

@pytest.mark.skip("Not a test")
def testsource(tests):
    source = '''
    unsigned int tests[{}][{}] = {{
'''.format(len(tests), len(tests[0]))

    for test in tests:
        testvector = ', '.join([to_string(t.value) for t in test])
        source += '''\
        {{ {} }},
'''.format(testvector)

    source += '''\
    };
'''
    return source

def bodysource(tests):
    body = """\
    for(int i = 0; i < {ntests}; i++) {{
        unsigned int* test = tests[i];
""".format(ntests=len(tests))
    inputs = []
    for i, val in enumerate(tests[0]):
        if isinstance(val, test_input):
            inputs.append(val)
            body += "        top->{key} = test[{i}];\n".format(key=val.name, i=i)

    input_printf_string = "\"[Test Iteration %d] Inputs: {inputs}\\n\", ".format(inputs=", ".join("{name}=%x".format(name=val.name) for val in inputs))
    input_printf_string += "i, "
    input_printf_string += ", ".join("test[{i}]".format(i=i) for i in range(len(inputs)))

    output_string = ""
    for i, output in enumerate(tests[0]):
        if isinstance(output, test_output):
            output_string += "        printf(\"    expected_{name}=%x, actual_{name}=%x\\n\", test[{i}], top->{name});\n".format(name=output.name, i=i)
            output_string += "        assert(top->{name} == test[{i}]);\n".format(name=output.name, i=i)

    return body + '''
        top->eval();
        printf({input_printf_string});
{output_string}
    }}
'''.format(input_printf_string=input_printf_string, output_string=output_string)

def harness(top_name, opcode, tests, has_clk=False):

    test = testsource(tests)
    body = bodysource(tests)
    step_body = ""
    if has_clk:
        step_body = """
    top->clk = 0;
    top->eval();
    top->clk = 1;
    top->eval();
"""
    return '''\
#include "V{top_name}.h"
#include "verilated.h"
#include <cassert>
#include <iostream>
#include <printf.h>

void step(V{top_name}* top) {{
    {step_body}
}}


int main(int argc, char **argv, char **env) {{
    Verilated::commandArgs(argc, argv);
    V{top_name}* top = new V{top_name};

    {test}

    top->op_code = {op};

    {body}

    delete top;
    std::cout << "Success" << std::endl;
    exit(0);
}}'''.format(test=test,body=body,top_name=top_name,op=opcode&0xff,step_body=step_body)


def compile(harness_name, top_name, opcode, tests, build_dir="build"):
    # print("========== BEGIN: Compiling verilator test harness ===========")
    verilatorcpp = harness(top_name, opcode, tests)
    with open(f'{build_dir}/{harness_name}.cpp', "w") as f:
        f.write(verilatorcpp)
    # print("========== DONE:  Compiling verilator test harness ===========")



def run_verilator_test(verilog_file_name, driver_name, top_module, build_dir="build"):
    if not os.path.isfile(os.path.join(build_dir, "obj_dir", f"V{top_module}.mk")):
        # print("========== BEGIN: Using verilator to generate test files =====")
        assert not subprocess.call('verilator -I../../../genesis_verif -Wno-fatal --cc {} --exe {}.cpp --top-module {}'.format(verilog_file_name, driver_name, top_module), cwd=build_dir, shell=True)
        # print("========== DONE:  Using verilator to generate test files =====")
    # print("========== BEGIN: Compiling verilator test ===================")
    assert not subprocess.call('make --silent -C obj_dir -j -f V{0}.mk V{0}'.format(top_module), cwd=build_dir, shell=True)
    # print("========== DONE:  Compiling verilator test ===================")
    # print("========== BEGIN: Running verilator test =====================")
    assert not subprocess.call('./obj_dir/V{}'.format(top_module), cwd=build_dir, shell=True)
    # print("========== DONE:  Running verilator test =====================")
