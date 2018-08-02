module top();

   reg [31:0] config_addr;
   reg [31:0] config_data;
   reg [31:0] read_data;

   reg        clk;
   reg        clk_en;
   reg        reset;
   reg        config_en;
   
   reg [15:0] pe_output_0;
   reg [15:0] in_0_0;
   reg [15:0] in_0_1;
   reg [15:0] in_1_0;
   reg [15:0] in_1_1;
   reg [15:0] in_2_0;
   reg [15:0] in_2_1;
   reg [15:0] in_3_0;
   reg [15:0] in_3_1; 

   reg [15:0] out_0_0;
   reg [15:0] out_0_1;
   reg [15:0] out_1_0;
   reg [15:0] out_1_1;
   reg [15:0] out_2_0;
   reg [15:0] out_2_1;
   reg [15:0] out_3_0;
   reg [15:0] out_3_1;

   always  
      #1 clk =   ~clk;

   initial begin
      #1 clk = 1'b0;
      #1 config_addr = 0;
      #1 config_en = 0;
      #1 clk_en    = 0; 

      // Test 1 - Check after reset
      #1 $display("read data before reset = %d", read_data);
      #1 reset = 0;
      #1 reset = 1;
      #1 reset = 0;
      #1 $display("read data after reset = %h", read_data);

      #1 $display ("-----");
      #1 $display ("DEBUG1: After Reset");
      #1 $display("read data after reset = %h", read_data);
      #1 assert(read_data == {{16{1'b0}},{16{1'b1}}}) $display ("ASSERT 1 PASSED"); 
      #1 $display ("-----"); 
      
      // Test 2 - Check after config is loaded
      #1 config_en = 1;
      #1 $display ("-----");
      #1 $display ("DEBUG2: Config loading");
      #1 config_data = 32'hABCD;
      #1 $display("read data after config loading = %h", read_data); 
      #1 assert(read_data == config_data) $display ("ASSERT 2 PASSED");      

      // Test 3  - Check when PE output is selected as SB output 
      #1 $display ("-----");
      #1 config_data = 32'hFFFF;
      #1 pe_output_0 = 46;
      #1 $display ("-----");
      #1 $display ("DEBUG3: PE input read"); 
      #1 $display("out_0_0 = %d", out_0_0);
      #1 $display("out_0_1 = %d", out_0_1);
      
      #1 pe_output_0 = 50;
 
      #1 $display("out_1_0 = %d", out_1_0);
      #1 $display("out_1_1 = %d", out_1_1);
      
      #1 pe_output_0 = 120;

      #1 $display("out_2_0 = %d", out_2_0);
      #1 $display("out_2_1 = %d", out_2_1);

      #1 pe_output_0 = 246;

      #1 $display("out_3_0 = %d", out_3_0);
      #1 $display("out_3_1 = %d", out_3_1); 
      #1 assert(out_1_1 == 246) $display ("ASSERT 3 PASSED"); 
      #1 $display ("-----"); 
      
      // Test 4 - Check no config loading when config_en is disabled
      #1 $display ("-----");
      #1 $display ("DEBUG4: Disabling config_en");
      #1 config_en = 0;
      #1 config_data = 32'hDD;
      #1 $display("read data after disabling config_en  = %d", read_data);
      #1 assert(read_data == 32'hFFFF) $display ("ASSERT 4 PASSED");
      #1 $display ("-----");

      // Test 5 - 3rd output of SB muxes are selected 
      #1 $display ("-----");
      #1 $display ("DEBUG5: MUX Select Test");
      #1 config_en = 1'b1; 
      #1 config_data = 32'hAAAA;
      #1 in_3_0 = 123;
      #1 in_3_1 = 456; 
      #1 in_2_0 = 789;
      #1 in_2_1 = 987; 
      #1 $display("out_0_0 = %d", out_0_0);
      #1 $display("out_0_1 = %d", out_0_1);
      #1 $display("out_1_0 = %d", out_1_0);
      #1 $display("out_1_1 = %d", out_1_1);
      #1 $display("out_2_0 = %d", out_2_0);
      #1 $display("out_2_1 = %d", out_2_1);
      #1 $display("out_3_0 = %d", out_3_0);
      #1 $display("out_3_1 = %d", out_3_1); 
      #1 $display("out_0_0 = %d", out_0_0);
      #1 $display("out_0_1 = %d", out_0_1); 
      #1 assert(out_0_1 == 456) $display ("ASSERT 5 PASSED");
      #1 $display ("-----");
  
      // Test 6 - Enable clk_en 
      #1 $display ("-----");      
      #1 $display ("DEBUG6: Enable clk_en");
      #1 config_data = 32'hDD;
      #1 config_en = 1'b0;
      #1 config_en = 1'b1;
      #1 config_data = 32'hAAAA;
      #1 clk_en = 1'b1;
      #1 in_3_0 = 321;
      #1 in_3_1 = 654;
      #1 in_2_0 = 987;
      #1 in_2_1 = 789;
      #1 $display("out_0_0 = %d", out_0_0);
      #1 $display("out_0_1 = %d", out_0_1);
      #1 $display("out_1_0 = %d", out_1_0);
      #1 $display("out_1_1 = %d", out_1_1);
      #1 $display("out_2_0 = %d", out_2_0);
      #1 $display("out_2_1 = %d", out_2_1);
      #1 $display("out_3_0 = %d", out_3_0);
      #1 $display("out_3_1 = %d", out_3_1);
      #1 $display("out_0_0 = %d", out_0_0);
      #1 $display("out_0_1 = %d", out_0_1);
      #1 assert(out_0_1 == 654) $display ("ASSERT 6 PASSED");
      #1 $display ("-----");
      $finish();


   end


   sb dut
  (
    .clk(clk),
    .clk_en(clk_en),
    .reset(reset),
    .pe_output_0(pe_output_0),
    .out_0_0(out_0_0),
    .in_0_0(in_0_0),
    .out_0_1(out_0_1),
    .in_0_1(in_0_1),
    .out_1_0(out_1_0),
    .in_1_0(in_1_0),
    .out_1_1(out_1_1),
    .in_1_1(in_1_1),
    .out_2_0(out_2_0),
    .in_2_0(in_2_0),
    .out_2_1(out_2_1),
    .in_2_1(in_2_1),
    .out_3_0(out_3_0),
    .in_3_0(in_3_0),
    .out_3_1(out_3_1),
    .in_3_1(in_3_1),
    .config_addr(config_addr),
    .config_data(config_data),
    .config_en(config_en),
    .read_data(read_data)
  );


endmodule
