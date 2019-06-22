module tb_Tile_PECore();
  reg [15:0] SB_T0_EAST_SB_IN_B16_0;
  reg [0:0] SB_T0_EAST_SB_IN_B1_0;
  reg [0:0] SB_T0_EAST_SB_OUT_B1;
  reg [15:0] SB_T0_EAST_SB_OUT_B16;
  reg [15:0] SB_T0_NORTH_SB_IN_B16_0;
  reg [0:0] SB_T0_NORTH_SB_IN_B1_0;
  reg [0:0] SB_T0_NORTH_SB_OUT_B1;
  reg [15:0] SB_T0_NORTH_SB_OUT_B16;
  reg [15:0] SB_T0_SOUTH_SB_IN_B16_0;
  reg [0:0] SB_T0_SOUTH_SB_IN_B1_0;
  reg [0:0] SB_T0_SOUTH_SB_OUT_B1;
  reg [15:0] SB_T0_SOUTH_SB_OUT_B16;
  reg [15:0] SB_T0_WEST_SB_IN_B16_0;
  reg [0:0] SB_T0_WEST_SB_IN_B1_0;
  reg [0:0] SB_T0_WEST_SB_OUT_B1;
  reg [15:0] SB_T0_WEST_SB_OUT_B16;
  reg [15:0] SB_T1_EAST_SB_IN_B16_0;
  reg [0:0] SB_T1_EAST_SB_IN_B1_0;
  reg [0:0] SB_T1_EAST_SB_OUT_B1;
  reg [15:0] SB_T1_EAST_SB_OUT_B16;
  reg [15:0] SB_T1_NORTH_SB_IN_B16_0;
  reg [0:0] SB_T1_NORTH_SB_IN_B1_0;
  reg [0:0] SB_T1_NORTH_SB_OUT_B1;
  reg [15:0] SB_T1_NORTH_SB_OUT_B16;
  reg [15:0] SB_T1_SOUTH_SB_IN_B16_0;
  reg [0:0] SB_T1_SOUTH_SB_IN_B1_0;
  reg [0:0] SB_T1_SOUTH_SB_OUT_B1;
  reg [15:0] SB_T1_SOUTH_SB_OUT_B16;
  reg [15:0] SB_T1_WEST_SB_IN_B16_0;
  reg [0:0] SB_T1_WEST_SB_IN_B1_0;
  reg [0:0] SB_T1_WEST_SB_OUT_B1;
  reg [15:0] SB_T1_WEST_SB_OUT_B16;
  reg  clk;
  reg  clk_out;
  reg [31:0] config_config_addr;
  reg [31:0] config_config_data;
  reg [31:0] config_out_config_addr;
  reg [31:0] config_out_config_data;
  reg [0:0] config_out_read;
  reg [0:0] config_out_write;
  reg [0:0] config_read;
  reg [0:0] config_write;
  reg [31:0] read_config_data;
  reg [31:0] read_config_data_in;
  reg  reset;
  reg  reset_out;
  reg [3:0] stall;
  reg [3:0] stall_out;
  reg [15:0] tile_id;
  supply1 VDD;
  supply0 VSS;
  wire VDD_SW;  
  always  
      #1 clk =   ~clk;

  initial begin
      // Reset = 0 
      #1 reset = 0;
      #1 clk = 1'b0;
      // Setting address to 0 is necessary for reset 
      #1 config_config_addr = 0;
      
      // ====================================== 
      // ====================================== 
      // TEST 1 - RESET TEST
      // Check if tile is turned ON after reset
      // ====================================== 
      // ====================================== 
      #1 $display("-----PG BEFORE RESET--------");
      #1 $display("VDD = %h", VDD); 
      #1 $display("VSS = %h", VSS);
      #1 $display("VDD_SW = %h", dut.VDD_SW);

      #1 $display("\n===================================");
      #1 $display("==== TEST1: TILE RESET ======"); 
      #1 $display("==================================="); 
      #1 $display("-----PG BEFORE RESET--------");
      #1 $display("VDD = %h", VDD);
      #1 $display("VSS = %h", VSS);
      #1 $display("VDD_SW = %h", dut.VDD_SW);
      #1 $display("-----------DATA BEFORE RESET -----------");    
      #1 $display("reset signal value = %h", dut.PowerDomainConfigReg_inst0.reset);
      #1 $display("PS register out value = %h", dut.PowerDomainConfigReg_inst0.ps_en_out);
 
      // Enable Reset 
      #1 $display("-----------DATA DURING RESET -----------");
      #20 reset = 1;
      #1 $display("reset signal value = %h", dut.PowerDomainConfigReg_inst0.reset);
      #1 $display("PS register out value = %h", dut.PowerDomainConfigReg_inst0.ps_en_out);
 
      // Disable Reset 
      #20; reset = 0;
      #10 $display("-----------DATA AFTER RESET -----------");
      #1 $display("reset signal value = %h", dut.PowerDomainConfigReg_inst0.reset);
      #1 $display("PS register out value = %h", dut.PowerDomainConfigReg_inst0.ps_en_out);

      #1 $display("-----PG AFTER RESET--------");
      #1 $display("VDD = %h", VDD); 
      #1 $display("VSS = %h", VSS);
      #1 $display("VDD_SW = %h", dut.VDD_SW);
      #1 $display("\n==================================="); 
      #1 $display("ASSERTION #1");
      #1 assert (dut.VDD_SW == 1'b1) $display ("ASSERTION 1 PASS: Tile is ON after reset");
   else $error("ASSERTION 1 FAIL: Tile didn't turn ON after reset"); 
      #1 $display("==================================="); 
      // ======================================
      // ======================================
     
      // ====================================== 
      // ====================================== 
      // TEST 2 - DISABLE PS REGISTER   
      // Check power switch register write 
      // ====================================== 
      // ======================================
      #1 $display("\n===================================");
      #1 $display("==== TEST2: DISABLE TILE  ======");
      #1 $display("===================================");   
      #1 $display("------------PS REGISTER DISABLE:--------------");
      #1 config_config_addr = 32'h00080000;
      #1 config_config_data = 32'hFFFFFFF1;
      #1 tile_id = 0; 
      #1 config_write = 1;
      #1 config_read = 0;
      #1 stall = 0;
      #1 read_config_data_in = 32'h0;
      #1 $display("config_config_addr = %h", config_config_addr);
      #1 $display("config_config_data = %h", config_config_data);
      #1 $display("config_out_config_addr = %h", config_out_config_addr);
      #1 $display("config_out_config_data = %h", config_out_config_data);
      #1 $display("VDD = %h", VDD);
      #1 $display("VSS = %h", VSS);
      #1 $display("VDD_SW = %h", dut.VDD_SW);
      #1 $display("\n===================================");
      #1 $display("ASSERTION #2");
      #1 assert (dut.PowerDomainConfigReg_inst0.ps_en_out  == 1'b1) $display ("ASSERTION 2 PASS: Tile is disabled correctly");
         else $error("ASSERTION 2 FAIL: Tile didn't get disabled");
      #1 $display("==================================="); 

      // ====================================== 
      // ====================================== 
      // TEST 3 - ENABLE PS REGISTER   
      // Check power switch register write 
      // ====================================== 
      // ======================================
      #1 $display("\n===================================");
      #1 $display("==== TEST3: ENABLE TILE  ======");
      #1 $display("===================================");
      #1 $display("------------PS REGISTER DISABLE:--------------");
      #1 config_config_addr = 32'h00080000;
      #1 config_config_data = 32'hFFFFFFF0;
      #1 tile_id = 0;
      #1 config_write = 1;
      #1 config_read = 0;
      #1 stall = 0;
      #1 read_config_data_in = 32'h0;
      #1 $display("config_config_addr = %h", config_config_addr);
      #1 $display("config_config_data = %h", config_config_data);
      #1 $display("config_out_config_addr = %h", config_out_config_addr);
      #1 $display("config_out_config_data = %h", config_out_config_data);
      #1 $display("VDD = %h", VDD);
      #1 $display("VSS = %h", VSS);
      #1 $display("VDD_SW = %h", dut.VDD_SW);
      #1 $display("\n===================================");
      #1 $display("ASSERTION #3");
      #1 assert (dut.VDD_SW == 1'h1) $display ("ASSERTION 3 PASS: Tile is enabled correctly");
         else $error("ASSERTION 1 FAIL: Tile didn't get enabled");
      #1 $display("===================================");

      // ====================================== 
      // ====================================== 
      // TEST 4 - VERIFY GLOBAL SIGNALS   
      // Check global signals are ON after tile is OFF  
      // ====================================== 
      // ====================================== 
      #1 $display("\n===================================");
      #1 $display("==== TEST4: GLOBAL SIGNAL EN  ======");
      #1 $display("==================================="); 
      #1 $display("-----DISABLE TILE and CHECK IF GLOBAL SIGNALS STILL ON--------");
      #1 config_config_addr = 32'h00080000;
      #1 config_config_data = 32'hFFFFFFF1;
      #1 tile_id = 0;  
      #1 config_write = 1;
      #1 config_read = 0;
      #1 stall = 0;
      #1 read_config_data_in = 32'hABCDEF01;
      #1 $display("All global signals are = clk_out: %h reset: %h config_out_config_addr: %h config_out_config_data: %h config_out_read: %h config_out_write: %h read_config_data: %h stall_out: %h", clk_out, reset_out, config_out_config_addr, config_out_config_data, config_out_read, config_out_write, read_config_data, stall_out);   
      #1 $display("VDD = %h", VDD);
      #1 $display("VSS = %h", VSS);
      #1 $display("VDD_SW = %h", dut.VDD_SW);
      #1 $display("\n===================================");
      #1 $display("ASSERTION #4");
      #1 assert (clk_out == clk) $display ("PASS: Clk is ON");
         else $error("Clk is OFF"); 
      #1 assert (reset_out == reset) $display ("PASS: Reset is ON");
         else $error("Reset is OFF"); 
      #1 assert (config_out_config_data == config_config_data) $display ("PASS: config_out_config_data is ON");
         else $error("FAIL: config_out_config_data is OFF");
      #1 assert (config_out_config_addr == config_config_addr) $display ("PASS: config_out_config_addr is ON");
         else $error("FAIL: config_out_config_addr is OFF");
      #1 assert (config_out_write == config_write) $display ("PASS: config_out_write is ON");
         else $error("FAIL: config_out_write is OFF");
      #1 assert (config_out_read == config_read) $display ("PASS: config_out_read is ON");
         else $error("FAIL: config_read is OFF"); 
      #1 assert (stall_out == stall) $display ("PASS: stall_out is ON");
         else $error("FAIL: stall_out is OFF");  
      #1 assert (read_config_data == read_config_data_in) $display ("PASS: read_config_data is ON");
         else $error("FAIL: read_config_data is OFF"); 
      #1 $display("===================================");
      
      // ====================================== 
      // ====================================== 
      // TEST 5 - VERIFY NO OTHER ADDR ENABLES PS REG   
      // Check if write to another register doesn't enable PS  
      // ====================================== 
      // ======================================

      #1 $display("\n===================================");
      #1 $display("==== TEST 5 - VERIFY NO OTHER ADDR ENABLES PS REG  ======");
      #1 $display("==================================="); 
      #1 config_write = 1;
      #1 config_config_addr = 32'h00070000;
      #1 config_config_data = 32'h0;
      #1 tile_id = 0;
      #1 config_read = 0;
      #1 stall = 0;
      #1 $display("VDD = %h", VDD);
      #1 $display("VSS = %h", VSS);
      #1 $display("VDD_SW = %h", dut.VDD_SW);
      #1 $display("\n===================================");
      #1 $display("ASSERTION #5");
      #1 assert (dut.PowerDomainConfigReg_inst0.ps_en_out == 1'b1) $display ("ASSERTION 5 PASS: As expected, PS register is not enabled");
         else $error("ASSERTION 5 FAIL: PS register enabled unexpectedly");
      #1 $display("===================================");

      // ====================================== 
      // ====================================== 
      // TEST 6 - AOI-CONST-MUX OUT CHECKS    
      // Check aoi-const-mux intermediate and final output is zero when sel==height  
      // ====================================== 
      // ======================================
      #1 $display("\n===================================");
      #1 $display("==== TEST 6 - AOI-CONST-MUX OUT CHECKS  ======");
      #1 $display("==================================="); 
      #1 config_config_addr = 32'h00080000;
      #1 config_config_data = 32'hFFFFFFF0;
      #1 tile_id = 0;
      #1 config_write = 1;
      #1 $display("VDD = %h", VDD);
      #1 $display("VSS = %h", VSS);
      #1 $display("VDD_SW = %h", dut.VDD_SW);
      #1 config_config_addr = 32'h00040000;
      #1 config_config_data = 32'd20;
      #1 config_write = 1;
      #1 $display("Sel = %d",dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.S);
      #1 $display("AOI-CONST MUX OUT = %h", dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.O);
      #1 $display("Inter AOI-CONST MUX OUT = %h", dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.u_mux_logic.O0);
      #1 $display("\n===================================");
      #1 $display("ASSERTION #6");
      #1 assert (dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.O == 0) $display ("ASSERTION 6 PASS: Constant mux output generated when sel==height");
         else $error("ASSERTION 6 FAIL: AOI-Const Mux output incorrect when sel==height");
      #1 $display("ASSERTION #7");
      #1 assert (dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.u_mux_logic.O0 == 0 && dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.u_mux_logic.O1 == 0 && dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.u_mux_logic.O2 == 0 && dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.u_mux_logic.O3 == 0 && dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.u_mux_logic.O4 == 0 && dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.u_mux_logic.O5 == 0 && dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.u_mux_logic.O6 == 0 && dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.u_mux_logic.O7 == 0 && dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.u_mux_logic.O8 == 0 && dut.CB_data0.CB_data0.mux_aoi_const_20_16_inst0.u_mux_logic.O9 == 0) $display ("ASSERTION 7 PASS: X Prop is terminated at 1st stage of MUX");
         else $error("ASSERTION 7 FAIL : X Prop is not terminated at 1st stage of MUX");

      #1 $display("===================================");
    
      // ====================================== 
      // TEST 7 - AOI-MUX OUT CHECKS    
      // Check aoi-mux intermediate output is zero when sel==height  
      // ====================================== 
      // ======================================
      //#1 $display("\n===================================");
      //#1 $display("==== TEST 7 - AOI-MUX OUT CHECKS  ======");
      //#1 $display("===================================");
      //#1 config_config_addr = 32'h00080000;
      //#1 config_config_data = 32'hFFFFFFF0;
      //#1 tile_id = 0;
      //#1 config_write = 1;
      //#1 $display("VDD = %h", VDD);
      //#1 $display("VSS = %h", VSS);
      //#1 $display("VDD_SW = %h", VDD_SW);
      //#1 config_config_addr = 32'h00070008;
      //#1 config_config_data = 32'd1;
      //#1 config_write = 1;
      //#1 $display("Sel = %d", dut.SB_ID0_5TRACKS_B16_PE.MUX_SB_T0_EAST_SB_OUT_B16.mux_aoi_4_16_inst0.O);
      //#1 assert (dut.SB_ID0_5TRACKS_B16_PE.MUX_SB_T0_EAST_SB_OUT_B16.mux_aoi_4_16_inst0.O == 0) $display ("ASSERTION 6 PASS: Constant mux output generated when sel==height");


end

  Tile_PE dut(
    .SB_T0_EAST_SB_IN_B16_0(SB_T0_EAST_SB_IN_B16_0),
    .SB_T0_EAST_SB_IN_B1_0(SB_T0_EAST_SB_IN_B1_0),
    .SB_T0_EAST_SB_OUT_B1(SB_T0_EAST_SB_OUT_B1),
    .SB_T0_EAST_SB_OUT_B16(SB_T0_EAST_SB_OUT_B16),
    .SB_T0_NORTH_SB_IN_B16_0(SB_T0_NORTH_SB_IN_B16_0),
    .SB_T0_NORTH_SB_IN_B1_0(SB_T0_NORTH_SB_IN_B1_0),
    .SB_T0_NORTH_SB_OUT_B1(SB_T0_NORTH_SB_OUT_B1),
    .SB_T0_NORTH_SB_OUT_B16(SB_T0_NORTH_SB_OUT_B16),
    .SB_T0_SOUTH_SB_IN_B16_0(SB_T0_SOUTH_SB_IN_B16_0),
    .SB_T0_SOUTH_SB_IN_B1_0(SB_T0_SOUTH_SB_IN_B1_0),
    .SB_T0_SOUTH_SB_OUT_B1(SB_T0_SOUTH_SB_OUT_B1),
    .SB_T0_SOUTH_SB_OUT_B16(SB_T0_SOUTH_SB_OUT_B16),
    .SB_T0_WEST_SB_IN_B16_0(SB_T0_WEST_SB_IN_B16_0),
    .SB_T0_WEST_SB_IN_B1_0(SB_T0_WEST_SB_IN_B1_0),
    .SB_T0_WEST_SB_OUT_B1(SB_T0_WEST_SB_OUT_B1),
    .SB_T0_WEST_SB_OUT_B16(SB_T0_WEST_SB_OUT_B16),
    .SB_T1_EAST_SB_IN_B16_0(SB_T1_EAST_SB_IN_B16_0),
    .SB_T1_EAST_SB_IN_B1_0(SB_T1_EAST_SB_IN_B1_0),
    .SB_T1_EAST_SB_OUT_B1(SB_T1_EAST_SB_OUT_B1),
    .SB_T1_EAST_SB_OUT_B16(SB_T1_EAST_SB_OUT_B16),
    .SB_T1_NORTH_SB_IN_B16_0(SB_T1_NORTH_SB_IN_B16_0),
    .SB_T1_NORTH_SB_IN_B1_0(SB_T1_NORTH_SB_IN_B1_0),
    .SB_T1_NORTH_SB_OUT_B1(SB_T1_NORTH_SB_OUT_B1),
    .SB_T1_NORTH_SB_OUT_B16(SB_T1_NORTH_SB_OUT_B16),
    .SB_T1_SOUTH_SB_IN_B16_0(SB_T1_SOUTH_SB_IN_B16_0),
    .SB_T1_SOUTH_SB_IN_B1_0(SB_T1_SOUTH_SB_IN_B1_0),
    .SB_T1_SOUTH_SB_OUT_B1(SB_T1_SOUTH_SB_OUT_B1),
    .SB_T1_SOUTH_SB_OUT_B16(SB_T1_SOUTH_SB_OUT_B16),
    .SB_T1_WEST_SB_IN_B16_0(SB_T1_WEST_SB_IN_B16_0),
    .SB_T1_WEST_SB_IN_B1_0(SB_T1_WEST_SB_IN_B1_0),
    .SB_T1_WEST_SB_OUT_B1(SB_T1_WEST_SB_OUT_B1),
    .SB_T1_WEST_SB_OUT_B16(SB_T1_WEST_SB_OUT_B16),
    .clk(clk),
    .clk_out(clk_out),
    .config_config_addr(config_config_addr),
    .config_config_data(config_config_data),
    .config_out_config_addr(config_out_config_addr),
    .config_out_config_data(config_out_config_data),
    .config_out_read(config_out_read),
    .config_out_write(config_out_write),
    .config_read(config_read),
    .config_write(config_write),
    .read_config_data(read_config_data),
    .read_config_data_in(read_config_data_in),
    .reset(reset),
    .reset_out(reset_out),
    .stall(stall),
    .stall_out(stall_out),
    .tile_id(tile_id),
    .VDD(VDD),
    .VSS(VSS)
    //.VDD_SW(VDD_SW)
  );
endmodule
