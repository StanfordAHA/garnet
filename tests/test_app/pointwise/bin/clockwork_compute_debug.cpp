hcompute_hw_input_global_wrapper_stencil() {
// _hw_input_stencil_1 added as input _hw_input_stencil_1
// connected _hw_input_stencil_1 to the output port
}

hcompute_mult_stencil() {
uint16_t _259 = (uint16_t)(2);
uint16_t _260 = _hw_input_global_wrapper_stencil_1 * _259;
// _hw_input_global_wrapper_stencil_1 added as input _hw_input_global_wrapper_stencil_1
// created const: const_p2__259 with name _259
// mula: self.in // mulb: _259 o: _260 with obitwidth:16
// connected _260 to the output port
}

hcompute_hw_output_stencil() {
// _mult_stencil_1 added as input _mult_stencil_1
// connected _mult_stencil_1 to the output port
}

