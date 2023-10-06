#include "clockwork_testscript.h"
#include "unoptimized_pointwise.h"
#include "hw_classes.h"
#include <fstream>
#include <vector>

void run_clockwork_program(RDAI_MemObject **mem_object_list) {
	// input and output memory objects
	uint16_t *hw_input_stencil = (uint16_t*) mem_object_list[0]->host_ptr;
	uint16_t *hw_output_stencil = (uint16_t*) mem_object_list[1]->host_ptr;

	// input and output stream declarations
	HWStream< hw_uint<16> > hw_input_stencil_stream;
	HWStream< hw_uint<16> > hw_output_stencil_stream;
	int idx = 0;

	// provision input stream hw_input_stencil_stream
	std::vector<uint16_t> hw_input_stencil_stream_tile(64*64);   idx=0;
	for (int l1 = 0; l1 < 64; l1++) {
	for (int l0 = 0; l0 < 64; l0++) {
		hw_uint<16> in_val;
		set_at<0, 16, 16>(in_val, hw_uint<16>(hw_input_stencil[((l1*64) + l0)]));
		hw_input_stencil_stream.write(in_val);
		hw_input_stencil_stream_tile[idx] = hw_input_stencil[((l1*64) + l0)];  idx += 1;
	} } 
	ofstream hw_input_stencil_file("bin/hw_input_stencil.leraw", ios::binary);
	hw_input_stencil_file.write(reinterpret_cast<const char *>(hw_input_stencil_stream_tile.data()),
		sizeof(hw_input_stencil_stream_tile[0]) * 64 * 64);
	hw_input_stencil_file.close();


	// invoke clockwork program
	unoptimized_pointwise(
		hw_input_stencil_stream,
		hw_output_stencil_stream
	);

	// provision output buffer
	std::vector<uint16_t> hw_output_stencil_stream_tile(64*64);   idx=0;
	for (int l1 = 0; l1 < 64; l1++) {
	for (int l0 = 0; l0 < 64; l0++) {
		hw_uint<16> actual = hw_output_stencil_stream.read();
		int actual_lane = actual.extract<0, 15>();
		hw_output_stencil[((l1*64) + l0)] = (uint16_t)(actual_lane);
		hw_output_stencil_stream_tile[idx] = hw_output_stencil[((l1*64) + l0)];  idx += 1;
	} } 
	ofstream hw_output_file("bin/hw_output.leraw", ios::binary);
	hw_output_file.write(reinterpret_cast<const char *>(hw_output_stencil_stream_tile.data()),
		sizeof(hw_output_stencil_stream_tile[0]) * 64 * 64);
	hw_output_file.close();
	ofstream hw_output_header_file("bin/hw_output_header.txt", ios::binary);
	hw_output_header_file << "P5" << std::endl;
	hw_output_header_file << "64 64" << std::endl;
	hw_output_header_file << "65535" << std::endl;
	hw_output_header_file.close();
}

