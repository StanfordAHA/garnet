#pragma once
#include "hw_classes.h"
#include "clockwork_standard_compute_units.h"


//store is: hw_input_global_wrapper.stencil(hw_input_global_wrapper_s0_x_x, hw_input_global_wrapper_s0_y) = hw_input.stencil(hw_input_global_wrapper_s0_x_x, hw_input_global_wrapper_s0_y)
hw_uint<16> hcompute_hw_input_global_wrapper_stencil(hw_uint<16>& hw_input_stencil) {
  uint16_t _hw_input_stencil_1 = (uint16_t) (hw_input_stencil.extract<0, 15>());

  return _hw_input_stencil_1;
}

//store is: mult.stencil(mult_s0_x_x, mult_s0_y) = (hw_input_global_wrapper.stencil(mult_s0_x_x, mult_s0_y)*(uint16)2)
hw_uint<16> hcompute_mult_stencil(hw_uint<16>& hw_input_global_wrapper_stencil) {
  uint16_t _hw_input_global_wrapper_stencil_1 = (uint16_t) (hw_input_global_wrapper_stencil.extract<0, 15>());

  uint16_t _257 = (uint16_t)(2);
  uint16_t _258 = _hw_input_global_wrapper_stencil_1 * _257;
  return _258;
}

//store is: hw_output.stencil(hw_output_s0_x_xi_xi, hw_output_s0_y_yi) = mult.stencil(hw_output_s0_x_xi_xi, hw_output_s0_y_yi)
hw_uint<16> hcompute_hw_output_stencil(hw_uint<16>& mult_stencil) {
  uint16_t _mult_stencil_1 = (uint16_t) (mult_stencil.extract<0, 15>());

  return _mult_stencil_1;
}

