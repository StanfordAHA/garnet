module Zircon (
	input [12:0] axi4_slave_araddr,
    output axi4_slave_arready,
    input axi4_slave_arvalid,
    input [12:0] axi4_slave_awaddr,
    output axi4_slave_awready,
    input axi4_slave_awvalid,
    input axi4_slave_bready,
    output [1:0] axi4_slave_bresp,
    output axi4_slave_bvalid,
    output [31:0] axi4_slave_rdata,
    input axi4_slave_rready,
    output [1:0] axi4_slave_rresp,
    output axi4_slave_rvalid,
    input [31:0] axi4_slave_wdata,
    output axi4_slave_wready,
    input axi4_slave_wvalid,
    output cgra_running_clk_out,
    input clk_in,
    output interrupt,
    input jtag_tck,
    input jtag_tdi,
    output jtag_tdo,
    input jtag_tms,
    input jtag_trst_n,
    input [20:0] proc_packet_rd_addr,
    output [63:0] proc_packet_rd_data,
    output proc_packet_rd_data_valid,
    input proc_packet_rd_en,
    input [20:0] proc_packet_wr_addr,
    input [63:0] proc_packet_wr_data,
    input proc_packet_wr_en,
    input [7:0] proc_packet_wr_strb,
    input reset_in,

    // Axi for matrix unit
    output         auto_axi_in_aw_ready,
    input          auto_axi_in_aw_valid,
    input          auto_axi_in_aw_bits_id,
    input  [29:0]  auto_axi_in_aw_bits_addr,
    input  [7:0]   auto_axi_in_aw_bits_len,
    input  [2:0]   auto_axi_in_aw_bits_size,
    output         auto_axi_in_w_ready,
    input          auto_axi_in_w_valid,
    input  [63:0]  auto_axi_in_w_bits_data,
    input  [7:0]   auto_axi_in_w_bits_strb,
    input          auto_axi_in_w_bits_last,
    input          auto_axi_in_b_ready,
    output         auto_axi_in_b_valid,
    output         auto_axi_in_ar_ready,
    input          auto_axi_in_ar_valid,
    input          auto_axi_in_ar_bits_id,
    input  [29:0]  auto_axi_in_ar_bits_addr,
    input  [7:0]   auto_axi_in_ar_bits_len,
    input  [2:0]   auto_axi_in_ar_bits_size,
    input          auto_axi_in_r_ready,
    output         auto_axi_in_r_valid,
    output         auto_axi_in_r_bits_id,
    output [63:0]  auto_axi_in_r_bits_data,
    output [1:0]   auto_axi_in_r_bits_resp,
    output         auto_axi_in_r_bits_last
);

	// Interconnect declarations
    logic [15:0] mu2cgra [31:0];
	  logic [511:0] outputsFromSystolicArray_dat;
    logic mu2cgra_valid;
    logic cgra2mu_ready;

    logic [20:0] auto_unified_out_a_bits_address;
    logic auto_unified_out_a_valid;
    logic auto_unified_out_a_ready;
    logic [3:0] auto_unified_out_a_bits_size;
    logic [6:0] auto_unified_out_a_bits_source;
    logic auto_unified_out_d_ready;
    logic auto_unified_out_d_valid;
    logic [2:0] auto_unified_out_d_bits_opcode;
    logic [3:0] auto_unified_out_d_bits_size;
    logic [6:0] auto_unified_out_d_bits_source;
    logic [255:0] auto_unified_out_d_bits_data;

    // pipelined interconnect declarations
    logic [20:0] auto_unified_out_a_bits_address_pipelined;
    logic auto_unified_out_a_valid_pipelined;
    logic auto_unified_out_a_ready_pipelined;
    logic [3:0] auto_unified_out_a_bits_size_pipelined;
    logic [6:0] auto_unified_out_a_bits_source_pipelined;

    logic auto_unified_out_d_ready_pipelined;
    logic auto_unified_out_d_valid_pipelined;
    logic [2:0] auto_unified_out_d_bits_opcode_pipelined;
    logic [3:0] auto_unified_out_d_bits_size_pipelined;
    logic [6:0] auto_unified_out_d_bits_source_pipelined;
    logic [255:0] auto_unified_out_d_bits_data_pipelined;


    Garnet garnet_1 (
        // clk/reset/interrupt
        .clk_in              (clk_in),
        .reset_in            (reset_in),
        .interrupt           (interrupt),
        .cgra_running_clk_out(cgra_running_clk_out),

        // proc ifc
        .proc_packet_wr_en        (proc_packet_wr_en),
        .proc_packet_wr_strb      (proc_packet_wr_strb),
        .proc_packet_wr_addr      (proc_packet_wr_addr),
        .proc_packet_wr_data      (proc_packet_wr_data),
        .proc_packet_rd_en        (proc_packet_rd_en),
        .proc_packet_rd_addr      (proc_packet_rd_addr),
        .proc_packet_rd_data      (proc_packet_rd_data),
        .proc_packet_rd_data_valid(proc_packet_rd_data_valid),

        // axi4-lite ifc
        .axi4_slave_araddr (axi4_slave_araddr),
        .axi4_slave_arready(axi4_slave_arready),
        .axi4_slave_arvalid(axi4_slave_arvalid),
        .axi4_slave_awaddr (axi4_slave_awaddr),
        .axi4_slave_awready(axi4_slave_awready),
        .axi4_slave_awvalid(axi4_slave_awvalid),
        .axi4_slave_bready (axi4_slave_bready),
        .axi4_slave_bresp  (axi4_slave_bresp),
        .axi4_slave_bvalid (axi4_slave_bvalid),
        .axi4_slave_rdata  (axi4_slave_rdata),
        .axi4_slave_rready (axi4_slave_rready),
        .axi4_slave_rresp  (axi4_slave_rresp),
        .axi4_slave_rvalid (axi4_slave_rvalid),
        .axi4_slave_wdata  (axi4_slave_wdata),
        .axi4_slave_wready (axi4_slave_wready),
        .axi4_slave_wvalid (axi4_slave_wvalid),

        // jtag ifc
        .jtag_tck   (jtag_tck),
        .jtag_tdi   (jtag_tdi),
        .jtag_tdo   (jtag_tdo),
        .jtag_tms   (jtag_tms),
        .jtag_trst_n(jtag_trst_n),

        // matrix unit-global buffer ifc
        .mu_tl_addr_in(auto_unified_out_a_bits_address_pipelined),
        .mu_tl_rq_in_vld(auto_unified_out_a_valid_pipelined),
        .mu_tl_rq_in_rdy(auto_unified_out_a_ready_pipelined),
        .mu_tl_size_in(auto_unified_out_a_bits_size_pipelined),
        .mu_tl_source_in(auto_unified_out_a_bits_source_pipelined),
        .mu_tl_data_out(auto_unified_out_d_bits_data),
        .mu_tl_resp_out_vld(auto_unified_out_d_valid),
        .mu_tl_resp_out_rdy(auto_unified_out_d_ready),
        .mu_tl_size_out(auto_unified_out_d_bits_size),
        .mu_tl_source_out(auto_unified_out_d_bits_source),
        .mu_tl_opcode_out(auto_unified_out_d_bits_opcode),

        // matrix unit-cgra tile array ifc
        .mu2cgra_valid (mu2cgra_valid),
        .cgra2mu_ready (cgra2mu_ready),
        .mu2cgra(mu2cgra)
    );

	// interconnect
	genvar i;
	generate
		for (i = 0; i < 32; i = i + 1) begin : assign_mu2cgra
			assign mu2cgra[i] = outputsFromSystolicArray_dat[(i+1)*16-1:i*16];
		end
	endgenerate


    MatrixUnitWrapper matrixUnit_1 (
        // clk /reset
        .auto_clock_in_clock(clk_in),
        .auto_clock_in_reset(reset_in),

        // Unified MU-GLB ifc
        .auto_unified_out_a_ready(auto_unified_out_a_ready),
        .auto_unified_out_a_valid(auto_unified_out_a_valid),
        .auto_unified_out_a_bits_opcode( /* UNUSED */ ),
        .auto_unified_out_a_bits_size(auto_unified_out_a_bits_size),
        .auto_unified_out_a_bits_source(auto_unified_out_a_bits_source),
        .auto_unified_out_a_bits_address(auto_unified_out_a_bits_address),
        .auto_unified_out_a_bits_mask( /* UNUSED */ ),
        .auto_unified_out_d_ready(auto_unified_out_d_ready_pipelined),
        .auto_unified_out_d_valid(auto_unified_out_d_valid_pipelined),
        .auto_unified_out_d_bits_opcode(auto_unified_out_d_bits_opcode_pipelined),
        .auto_unified_out_d_bits_size(auto_unified_out_d_bits_size_pipelined),
        .auto_unified_out_d_bits_source(auto_unified_out_d_bits_source_pipelined),
        .auto_unified_out_d_bits_data(auto_unified_out_d_bits_data_pipelined),

        // MU-CGRA tile array ifc (fused outputs)
        .io_outputsFromSystolicArray_vld(mu2cgra_valid),
        .io_outputsFromSystolicArray_rdy(cgra2mu_ready),
        .io_outputsFromSystolicArray_dat(outputsFromSystolicArray_dat),

        // MU Axi ifc
        .auto_axi_in_aw_ready(auto_axi_in_aw_ready),
        .auto_axi_in_aw_valid(auto_axi_in_aw_valid),
        .auto_axi_in_aw_bits_id(auto_axi_in_aw_bits_id),
        .auto_axi_in_aw_bits_addr(auto_axi_in_aw_bits_addr),
        .auto_axi_in_aw_bits_len(auto_axi_in_aw_bits_len),
        .auto_axi_in_aw_bits_size(auto_axi_in_aw_bits_size),
        .auto_axi_in_w_ready(auto_axi_in_w_ready),
        .auto_axi_in_w_valid(auto_axi_in_w_valid),
        .auto_axi_in_w_bits_data(auto_axi_in_w_bits_data),
        .auto_axi_in_w_bits_strb(auto_axi_in_w_bits_strb),
        .auto_axi_in_w_bits_last(auto_axi_in_w_bits_last),
        .auto_axi_in_b_ready(auto_axi_in_b_ready),
        .auto_axi_in_b_valid(auto_axi_in_b_valid),
        .auto_axi_in_ar_ready(auto_axi_in_ar_ready),
        .auto_axi_in_ar_valid(auto_axi_in_ar_valid),
        .auto_axi_in_ar_bits_id(auto_axi_in_ar_bits_id),
        .auto_axi_in_ar_bits_addr(auto_axi_in_ar_bits_addr),
        .auto_axi_in_ar_bits_len(auto_axi_in_ar_bits_len),
        .auto_axi_in_ar_bits_size(auto_axi_in_ar_bits_size),
        .auto_axi_in_r_ready(auto_axi_in_r_ready),
        .auto_axi_in_r_valid(auto_axi_in_r_valid),
        .auto_axi_in_r_bits_id(auto_axi_in_r_bits_id),
        .auto_axi_in_r_bits_data(auto_axi_in_r_bits_data),
        .auto_axi_in_r_bits_resp(auto_axi_in_r_bits_resp),
        .auto_axi_in_r_bits_last(auto_axi_in_r_bits_last)
    );

    mu_glb_pipeline_fifo_d_2_w_21 zircon_addr_req_pipeline (
        .clk(clk_in),
        .data_in(auto_unified_out_a_bits_address),
        .pop(auto_unified_out_a_ready_pipelined),
        .push(auto_unified_out_a_valid),
        .reset(reset_in),
        .data_out(auto_unified_out_a_bits_address_pipelined),
        .empty(addr_req_pipeline_empty),
        .full(addr_req_pipeline_full)
    );

    assign auto_unified_out_a_valid_pipelined = ~addr_req_pipeline_empty;
    assign auto_unified_out_a_ready = ~addr_req_pipeline_full;

    mu_glb_pipeline_fifo_d_2_w_4 zircon_size_req_pipeline (
        .clk(clk_in),
        .data_in(auto_unified_out_a_bits_size),
        .pop(auto_unified_out_a_ready_pipelined),
        .push(auto_unified_out_a_valid),
        .reset(reset_in),
        .data_out(auto_unified_out_a_bits_size_pipelined),
        .empty(/* UNUSED */),
        .full(/* UNUSED */)
    );

    mu_glb_pipeline_fifo_d_2_w_7 zircon_source_req_pipeline (
        .clk(clk_in),
        .data_in(auto_unified_out_a_bits_source),
        .pop(auto_unified_out_a_ready_pipelined),
        .push(auto_unified_out_a_valid),
        .reset(reset_in),
        .data_out(auto_unified_out_a_bits_source_pipelined),
        .empty(/* UNUSED */),
        .full(/* UNUSED */)
    );

    mu_glb_pipeline_fifo_d_2_w_256 zircon_data_resp_pipeline (
        .clk(clk_in),
        .data_in(auto_unified_out_d_bits_data),
        .pop(auto_unified_out_d_ready_pipelined),
        .push(auto_unified_out_d_valid),
        .reset(reset_in),
        .data_out(auto_unified_out_d_bits_data_pipelined),
        .empty(data_resp_pipeline_empty),
        .full(data_resp_pipeline_full)
    );

    assign auto_unified_out_d_valid_pipelined = ~data_resp_pipeline_empty;
    assign auto_unified_out_d_ready = ~data_resp_pipeline_full;

    mu_glb_pipeline_fifo_d_2_w_3 zircon_opcode_resp_pipeline (
        .clk(clk_in),
        .data_in(auto_unified_out_d_bits_opcode),
        .pop(auto_unified_out_d_ready_pipelined),
        .push(auto_unified_out_d_valid),
        .reset(reset_in),
        .data_out(auto_unified_out_d_bits_opcode_pipelined),
        .empty(/* UNUSED */),
        .full(/* UNUSED */)
    );

    mu_glb_pipeline_fifo_d_2_w_7 zircon_source_resp_pipeline (
        .clk(clk_in),
        .data_in(auto_unified_out_d_bits_source),
        .pop(auto_unified_out_d_ready_pipelined),
        .push(auto_unified_out_d_valid),
        .reset(reset_in),
        .data_out(auto_unified_out_d_bits_source_pipelined),
        .empty(/* UNUSED */),
        .full(/* UNUSED */)
    );

    mu_glb_pipeline_fifo_d_2_w_4 zircon_size_resp_pipeline (
        .clk(clk_in),
        .data_in(auto_unified_out_d_bits_size),
        .pop(auto_unified_out_d_ready_pipelined),
        .push(auto_unified_out_d_valid),
        .reset(reset_in),
        .data_out(auto_unified_out_d_bits_size_pipelined),
        .empty(/* UNUSED */),
        .full(/* UNUSED */)
    );
endmodule


module mu_glb_pipeline_fifo_d_2_w_21 #(
  parameter data_width = 16'h15
)
(
  input logic clk,
  input logic [data_width-1:0] data_in,
  input logic pop,
  input logic push,
  input logic reset,
  output logic [data_width-1:0] data_out,
  output logic empty,
  output logic full
);

logic [1:0] num_items;
logic rd_ptr;
logic read;
logic [1:0][data_width-1:0] reg_array;
logic wr_ptr;
logic write;
assign full = num_items == 2'h2;
assign empty = num_items == 2'h0;
assign read = pop & (~empty);
assign write = push & (~full);

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    num_items <= 2'h0;
  end
  else if (write & (~read)) begin
    num_items <= num_items + 2'h1;
  end
  else if ((~write) & read) begin
    num_items <= num_items - 2'h1;
  end
  else num_items <= num_items;
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    reg_array <= 42'h0;
  end
  else if (write) begin
    reg_array[wr_ptr] <= data_in;
  end
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    wr_ptr <= 1'h0;
  end
  else if (write) begin
    if (wr_ptr == 1'h1) begin
      wr_ptr <= 1'h0;
    end
    else wr_ptr <= wr_ptr + 1'h1;
  end
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    rd_ptr <= 1'h0;
  end
  else if (read) begin
    if (rd_ptr == 1'h1) begin
      rd_ptr <= 1'h0;
    end
    else rd_ptr <= rd_ptr + 1'h1;
  end
end
always_comb begin
  data_out = reg_array[rd_ptr];
end
endmodule   // mu_glb_pipeline_fifo_d_2_w_21


module mu_glb_pipeline_fifo_d_2_w_4 #(
  parameter data_width = 16'h4
)
(
  input logic clk,
  input logic [data_width-1:0] data_in,
  input logic pop,
  input logic push,
  input logic reset,
  output logic [data_width-1:0] data_out,
  output logic empty,
  output logic full
);

logic [1:0] num_items;
logic rd_ptr;
logic read;
logic [1:0][data_width-1:0] reg_array;
logic wr_ptr;
logic write;
assign full = num_items == 2'h2;
assign empty = num_items == 2'h0;
assign read = pop & (~empty);
assign write = push & (~full);

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    num_items <= 2'h0;
  end
  else if (write & (~read)) begin
    num_items <= num_items + 2'h1;
  end
  else if ((~write) & read) begin
    num_items <= num_items - 2'h1;
  end
  else num_items <= num_items;
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    reg_array <= 8'h0;
  end
  else if (write) begin
    reg_array[wr_ptr] <= data_in;
  end
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    wr_ptr <= 1'h0;
  end
  else if (write) begin
    if (wr_ptr == 1'h1) begin
      wr_ptr <= 1'h0;
    end
    else wr_ptr <= wr_ptr + 1'h1;
  end
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    rd_ptr <= 1'h0;
  end
  else if (read) begin
    if (rd_ptr == 1'h1) begin
      rd_ptr <= 1'h0;
    end
    else rd_ptr <= rd_ptr + 1'h1;
  end
end
always_comb begin
  data_out = reg_array[rd_ptr];
end
endmodule   // mu_glb_pipeline_fifo_d_2_w_4

module mu_glb_pipeline_fifo_d_2_w_7 #(
  parameter data_width = 16'h7
)
(
  input logic clk,
  input logic [data_width-1:0] data_in,
  input logic pop,
  input logic push,
  input logic reset,
  output logic [data_width-1:0] data_out,
  output logic empty,
  output logic full
);

logic [1:0] num_items;
logic rd_ptr;
logic read;
logic [1:0][data_width-1:0] reg_array;
logic wr_ptr;
logic write;
assign full = num_items == 2'h2;
assign empty = num_items == 2'h0;
assign read = pop & (~empty);
assign write = push & (~full);

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    num_items <= 2'h0;
  end
  else if (write & (~read)) begin
    num_items <= num_items + 2'h1;
  end
  else if ((~write) & read) begin
    num_items <= num_items - 2'h1;
  end
  else num_items <= num_items;
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    reg_array <= 14'h0;
  end
  else if (write) begin
    reg_array[wr_ptr] <= data_in;
  end
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    wr_ptr <= 1'h0;
  end
  else if (write) begin
    if (wr_ptr == 1'h1) begin
      wr_ptr <= 1'h0;
    end
    else wr_ptr <= wr_ptr + 1'h1;
  end
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    rd_ptr <= 1'h0;
  end
  else if (read) begin
    if (rd_ptr == 1'h1) begin
      rd_ptr <= 1'h0;
    end
    else rd_ptr <= rd_ptr + 1'h1;
  end
end
always_comb begin
  data_out = reg_array[rd_ptr];
end
endmodule   // mu_glb_pipeline_fifo_d_2_w_7


module mu_glb_pipeline_fifo_d_2_w_3 #(
  parameter data_width = 16'h3
)
(
  input logic clk,
  input logic [data_width-1:0] data_in,
  input logic pop,
  input logic push,
  input logic reset,
  output logic [data_width-1:0] data_out,
  output logic empty,
  output logic full
);

logic [1:0] num_items;
logic rd_ptr;
logic read;
logic [1:0][data_width-1:0] reg_array;
logic wr_ptr;
logic write;
assign full = num_items == 2'h2;
assign empty = num_items == 2'h0;
assign read = pop & (~empty);
assign write = push & (~full);

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    num_items <= 2'h0;
  end
  else if (write & (~read)) begin
    num_items <= num_items + 2'h1;
  end
  else if ((~write) & read) begin
    num_items <= num_items - 2'h1;
  end
  else num_items <= num_items;
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    reg_array <= 6'h0;
  end
  else if (write) begin
    reg_array[wr_ptr] <= data_in;
  end
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    wr_ptr <= 1'h0;
  end
  else if (write) begin
    if (wr_ptr == 1'h1) begin
      wr_ptr <= 1'h0;
    end
    else wr_ptr <= wr_ptr + 1'h1;
  end
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    rd_ptr <= 1'h0;
  end
  else if (read) begin
    if (rd_ptr == 1'h1) begin
      rd_ptr <= 1'h0;
    end
    else rd_ptr <= rd_ptr + 1'h1;
  end
end
always_comb begin
  data_out = reg_array[rd_ptr];
end
endmodule   // mu_glb_pipeline_fifo_d_2_w_3

module mu_glb_pipeline_fifo_d_2_w_256 #(
  parameter data_width = 16'h100
)
(
  input logic clk,
  input logic [data_width-1:0] data_in,
  input logic pop,
  input logic push,
  input logic reset,
  output logic [data_width-1:0] data_out,
  output logic empty,
  output logic full
);

logic [1:0] num_items;
logic rd_ptr;
logic read;
logic [1:0][data_width-1:0] reg_array;
logic wr_ptr;
logic write;
assign full = num_items == 2'h2;
assign empty = num_items == 2'h0;
assign read = pop & (~empty);
assign write = push & (~full);

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    num_items <= 2'h0;
  end
  else if (write & (~read)) begin
    num_items <= num_items + 2'h1;
  end
  else if ((~write) & read) begin
    num_items <= num_items - 2'h1;
  end
  else num_items <= num_items;
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    reg_array <= 512'h0;
  end
  else if (write) begin
    reg_array[wr_ptr] <= data_in;
  end
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    wr_ptr <= 1'h0;
  end
  else if (write) begin
    if (wr_ptr == 1'h1) begin
      wr_ptr <= 1'h0;
    end
    else wr_ptr <= wr_ptr + 1'h1;
  end
end

always_ff @(posedge clk, posedge reset) begin
  if (reset) begin
    rd_ptr <= 1'h0;
  end
  else if (read) begin
    if (rd_ptr == 1'h1) begin
      rd_ptr <= 1'h0;
    end
    else rd_ptr <= rd_ptr + 1'h1;
  end
end
always_comb begin
  data_out = reg_array[rd_ptr];
end
endmodule   // mu_glb_pipeline_fifo_d_2_w_256