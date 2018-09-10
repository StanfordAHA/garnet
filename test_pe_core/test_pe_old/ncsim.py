def compile(name, opcode, tests):
    test_string = ""

    for test in tests:
        test_string += f"  op_a = {test[0]};\n"
        test_string += f"  op_b = {test[1]};\n"
        test_string += f"  #1\n"
        test_string += f"  if (res != {test[2]}) $display(\"Failed!\");\n"
        test_string += f"  #20\n"

    harness = """\
`timescale 1ns/1ns
module test_pe_comp_unq1_tb;
localparam WIDTH = 16;
reg [WIDTH-1:0] op_a;
reg [WIDTH-1:0] op_b;
wire [WIDTH-1:0] res;

initial begin
{tests}
  #20 $finish;
end


test_pe_comp_unq1 dut (
    .op_a(op_a),
    .op_b(op_b),
    .res(res),
    .op_code({opcode})
   );
endmodule
""".format(tests=test_string,opcode=opcode&0x1ff)
    with open('build/ncsim_'+name+'_tb.v', "w") as f:
        f.write(harness)
