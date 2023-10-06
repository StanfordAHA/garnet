#pragma once
#include "hw_classes.h"
#include "conv_3x3.h"


//store is: hw_input.stencil(hw_input_s0_x, hw_input_s0_y) = input_copy.stencil(hw_input_s0_x, hw_input_s0_y)
hw_uint<16> hcompute_hw_input_stencil(hw_uint<16>& input_copy_stencil) {
  uint16_t _input_copy_stencil_1 = (uint16_t) input_copy_stencil.extract<0, 15>();

  return _input_copy_stencil_1;
}

//store is: mult.stencil(mult_s0_x, mult_s0_y) = (hw_input.stencil(mult_s0_x, mult_s0_y)*(uint16)2)
hw_uint<16> hcompute_mult_stencil(hw_uint<16>& hw_input_stencil) {
  uint16_t _hw_input_stencil_1 = (uint16_t) hw_input_stencil.extract<0, 15>();

  uint16_t _257 = (uint16_t)(2);
  uint16_t _258 = _hw_input_stencil_1 * _257;
  return _258;
}

//store is: hw_output.stencil(hw_output_s0_x_xi, hw_output_s0_y_yi) = uint8(mult.stencil(hw_output_s0_x_xi, hw_output_s0_y_yi))
hw_uint<8> hcompute_hw_output_stencil(hw_uint<16>& mult_stencil) {
  uint16_t _mult_stencil_1 = (uint16_t) mult_stencil.extract<0, 15>();

  uint8_t _264 = (uint8_t)(_mult_stencil_1);
  return _264;
}

