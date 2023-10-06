)
{
#pragma HLS DATAFLOW
#pragma HLS INLINE region
#pragma HLS INTERFACE s_axilite port=return bundle=config
#pragma HLS INTERFACE s_axilite port=arg_0 bundle=config
#pragma HLS ARRAY_PARTITION variable=arg_0.value complete dim=0
#pragma HLS INTERFACE s_axilite port=arg_1 bundle=config
#pragma HLS ARRAY_PARTITION variable=arg_1.value complete dim=0

 // alias the arguments
 Stencil<uint16_t, 64, 64> &hw_input_stencil = arg_0;
 Stencil<uint16_t, 64, 64> &hw_output_stencil = arg_1;
[, ], [, ] // produce hw_input_global_wrapper.stencil
 for (int hw_input_global_wrapper_s0_y = 0; hw_input_global_wrapper_s0_y < 64; hw_input_global_wrapper_s0_y++)
 {
  for (int hw_input_global_wrapper_s0_x_x = 0; hw_input_global_wrapper_s0_x_x < 64; hw_input_global_wrapper_s0_x_x++)
  {
#pragma HLS PIPELINE II=1
   uint16_t _256 = _hw_input_stencil(_hw_input_global_wrapper_s0_x_x, _hw_input_global_wrapper_s0_y);
   _hw_input_global_wrapper_stencil(_hw_input_global_wrapper_s0_x_x, _hw_input_global_wrapper_s0_y) = _256;
  } // for hw_input_global_wrapper_s0_x_x
 } // for hw_input_global_wrapper_s0_y
 // consume hw_input_global_wrapper.stencil
[, ], [, ] // produce mult.stencil
 for (int mult_s0_y = 0; mult_s0_y < 64; mult_s0_y++)
 {
  for (int mult_s0_x_x = 0; mult_s0_x_x < 64; mult_s0_x_x++)
  {
#pragma HLS PIPELINE II=1
   uint16_t _261 = _hw_input_global_wrapper_stencil(_mult_s0_x_x, _mult_s0_y);
   uint16_t _262 = (uint16_t)(2);
   uint16_t _263 = _261 * _262;
   _mult_stencil(_mult_s0_x_x, _mult_s0_y) = _263;
  } // for mult_s0_x_x
 } // for mult_s0_y
 // consume mult.stencil
 for (int hw_output_s0_y_yi = 0; hw_output_s0_y_yi < 64; hw_output_s0_y_yi++)
 {
  for (int hw_output_s0_x_xi_xi = 0; hw_output_s0_x_xi_xi < 64; hw_output_s0_x_xi_xi++)
  {
#pragma HLS PIPELINE II=1
   uint16_t _264 = _mult_stencil(_hw_output_s0_x_xi_xi, _hw_output_s0_y_yi);
   _hw_output_stencil(_hw_output_s0_x_xi_xi, _hw_output_s0_y_yi) = _264;
  } // for hw_output_s0_x_xi_xi
 } // for hw_output_s0_y_yi
} // kernel hls_targetpointwise

