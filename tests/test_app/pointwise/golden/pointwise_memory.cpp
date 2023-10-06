#include "app.h"
#include "ubuffer.h"
#include "codegen.h"
#include "prog.h"

prog pointwise() {
  prog prg;
  prg.compute_unit_file = "pointwise_compute.h";
  prg.name = "pointwise";

// Stencil<uint16_t, 64, 64> &input_copy_stencil = arg_0;
  prg.add_input("input_copy_stencil");
  prg.buffer_port_widths["input_copy_stencil"] = 16;
// Stencil<uint8_t, 64, 64> &hw_output_stencil = arg_1;
  prg.add_output("hw_output_stencil");
  prg.buffer_port_widths["hw_output_stencil"] = 8;

////producing hw_input.stencil
  auto hw_input_s0_y = prg.add_loop("hw_input_s0_y", 0, 64);
  auto hw_input_s0_x = hw_input_s0_y->add_loop("hw_input_s0_x", 0, 64);

//store is: hw_input.stencil(hw_input_s0_x, hw_input_s0_y) = input_copy.stencil(hw_input_s0_x, hw_input_s0_y)
  auto hcompute_hw_input_stencil = hw_input_s0_x->add_op("op_hcompute_hw_input_stencil");
  hcompute_hw_input_stencil->add_function("hcompute_hw_input_stencil");
  hcompute_hw_input_stencil->add_load("input_copy_stencil", "hw_input_s0_y", "hw_input_s0_x");
  prg.buffer_port_widths["hw_input_stencil"] = 16;
  hcompute_hw_input_stencil->add_store("hw_input_stencil", "hw_input_s0_y", "hw_input_s0_x");

//consuming hw_input.stencil
////producing mult.stencil
  auto mult_s0_y = prg.add_loop("mult_s0_y", 0, 64);
  auto mult_s0_x = mult_s0_y->add_loop("mult_s0_x", 0, 64);

//store is: mult.stencil(mult_s0_x, mult_s0_y) = (hw_input.stencil(mult_s0_x, mult_s0_y)*(uint16)2)
  auto hcompute_mult_stencil = mult_s0_x->add_op("op_hcompute_mult_stencil");
  hcompute_mult_stencil->add_function("hcompute_mult_stencil");
  hcompute_mult_stencil->add_load("hw_input_stencil", "mult_s0_y", "mult_s0_x");
  prg.buffer_port_widths["mult_stencil"] = 16;
  hcompute_mult_stencil->add_store("mult_stencil", "mult_s0_y", "mult_s0_x");

//consuming mult.stencil
  auto hw_output_s0_y_yi = prg.add_loop("hw_output_s0_y_yi", 0, 64);
  auto hw_output_s0_x_xi = hw_output_s0_y_yi->add_loop("hw_output_s0_x_xi", 0, 64);

//store is: hw_output.stencil(hw_output_s0_x_xi, hw_output_s0_y_yi) = uint8(mult.stencil(hw_output_s0_x_xi, hw_output_s0_y_yi))
  auto hcompute_hw_output_stencil = hw_output_s0_x_xi->add_op("op_hcompute_hw_output_stencil");
  hcompute_hw_output_stencil->add_function("hcompute_hw_output_stencil");
  hcompute_hw_output_stencil->add_load("mult_stencil", "hw_output_s0_y_yi", "hw_output_s0_x_xi");
  hcompute_hw_output_stencil->add_store("hw_output_stencil", "hw_output_s0_y_yi", "hw_output_s0_x_xi");

  return prg;
}
