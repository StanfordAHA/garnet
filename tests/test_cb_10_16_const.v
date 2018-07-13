module top();

   reg [31:0] config_addr;
   reg [31:0] config_data;
   reg 	      config_en;
   reg [31:0] read_data;
      reg [31:0] read_data_magma;
   
   reg 	      clk;
   reg 	      reset;

   reg [15:0] out;
   reg [15:0] out_magma;   

   reg [15:0] in_0;
   reg [15:0] in_1;
   reg [15:0] in_2;
   reg [15:0] in_3;
   reg [15:0] in_4;

   reg [15:0] in_6;
   reg [15:0] in_7;
   reg [15:0] in_8;
   reg [15:0] in_9;   

   initial begin
      #1 config_addr = 0;
      #1 config_en = 0;

      #1 $display("read data before reset = %b", read_data);

      #1 reset = 0;
      #1 reset = 1;
      #1 reset = 0;

      #1 $display("read data after reset = %b", read_data);
      

      #1 config_en = 1;
      #1 config_data = 32'h1;
      
      #1 clk = 0;
      #1 clk = 1;

      #1 clk = 0;
      #1 clk = 1;
      
      #1 config_en = 0;

      #1 in_1 = 4;

      #1 $display("read data after config loading = %b", read_data);

      #2

      assert(out == 4);
      assert(out == out_magma);

      #1 in_9 = 345;

      #1 config_en = 1;
      #1 config_data = 32'h8;
      
      #1 clk = 0;
      #1 clk = 1;
      #1 clk = 0;

      #1 config_en = 0;

      #1 clk = 1;
      #1 clk = 0;

      assert(out == 345);
      assert(out == out_magma);

      #1 config_en = 1;

      #1 config_data = 32'd10;
      #1 config_data[19:4] = 7;

      #1 clk = 0;

      #1 clk = 1;
      #1 clk = 0;

      assert(read_data == config_data);
      assert(read_data_magma == config_data);      
      
      #1 config_en = 0;

      #1 config_data = 32'h0;

      #1 clk = 0;
      #1 clk = 1;
      #1 clk = 0;

      $display("read data = %b", read_data);
      $display("out = %d, %d", out, out_magma);

      assert(out == 7);
      assert(out == out_magma);  
      
      $finish();
   end


   cb
     connect_box(.clk(clk), .reset(reset), .config_addr(config_addr), .config_data(config_data), .config_en(config_en),
		  .in_0(in_0),
		  .in_1(in_1),
		  .in_2(in_2),
		  .in_3(in_3),
		  .in_4(in_4),

		  .in_6(in_6),
		  .in_7(in_7),
		  .in_8(in_8),
		  .in_9(in_9),

		 .read_data(read_data),

		  .out(out));

   connect_box_width_width_16_num_tracks_10_has_constant1_default_value7_feedthrough_outputs_1111101111   
     connect_box_magma(.clk(clk), .reset(reset), .config_addr(config_addr), .config_data(config_data), .config_en(config_en),
		  .in_0(in_0),
		  .in_1(in_1),
		  .in_2(in_2),
		  .in_3(in_3),
		  .in_4(in_4),

		  .in_6(in_6),
		  .in_7(in_7),
		  .in_8(in_8),
		  .in_9(in_9),

		 .read_data(read_data_magma),

		  .out(out_magma));
   
endmodule
