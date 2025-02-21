module CW_tap ( 
                tck, 
                trst_n, 
                tms, 
                tdi, 
                so, 
                bypass_sel, 
                sentinel_val, 
                clock_dr, 
                shift_dr,
                update_dr,
                tdo,
                tdo_en,
                tap_state,
                extest, 
                samp_load, 
                instructions, 
                sync_capture_en, 
                sync_update_dr,
                test
               );
   
//----------------------------------------------------------------------
// parameters declaration
//----------------------------------------------------------------------
   parameter width     = 2;
   parameter id        = 0;
   parameter version   = 0;
   parameter part      = 0;
   parameter man_num   = 0;
   parameter sync_mode = 0;
   

   parameter RESET      = 0;
   parameter IDLE       = 1;
   parameter SEL_DR_SC  = 2;
   parameter CAPTURE_DR = 3;
   parameter SHIFT_DR   = 4;
   parameter EXIT1_DR   = 5;
   parameter PAUSE_DR   = 6;
   parameter EXIT2_DR   = 7;
   parameter UPDATE_DR  = 8;
   parameter SEL_IR_SC  = 9;
   parameter CAPTURE_IR = 10;
   parameter SHIFT_IR   = 11;
   parameter EXIT1_IR   = 12;
   parameter PAUSE_IR   = 13;
   parameter EXIT2_IR   = 14;
   parameter UPDATE_IR  = 15;


   parameter RESET_STATE      = 16'b0000000000000001;
   parameter IDLE_STATE       = 16'b0000000000000010;
   parameter SEL_DR_SC_STATE  = 16'b0000000000000100;
   parameter CAPTURE_DR_STATE = 16'b0000000000001000;
   parameter SHIFT_DR_STATE   = 16'b0000000000010000;
   parameter EXIT1_DR_STATE   = 16'b0000000000100000;
   parameter PAUSE_DR_STATE   = 16'b0000000001000000;
   parameter EXIT2_DR_STATE   = 16'b0000000010000000;
   parameter UPDATE_DR_STATE  = 16'b0000000100000000;
   parameter SEL_IR_SC_STATE  = 16'b0000001000000000;
   parameter CAPTURE_IR_STATE = 16'b0000010000000000;
   parameter SHIFT_IR_STATE   = 16'b0000100000000000;
   parameter EXIT1_IR_STATE   = 16'b0001000000000000;
   parameter PAUSE_IR_STATE   = 16'b0010000000000000;
   parameter EXIT2_IR_STATE   = 16'b0100000000000000;
   parameter UPDATE_IR_STATE  = 16'b1000000000000000; 

//----------------------------------------------------------------------
// input declaration
//----------------------------------------------------------------------
   input                 tck;
   input                 trst_n;
   input                 tms;
   input                 tdi;
   input                 so;
   input                 bypass_sel;
   input [(width - 2):0] sentinel_val;
   input                 test;

//----------------------------------------------------------------------
// output declaration
//----------------------------------------------------------------------
   output                 clock_dr;
   output                 shift_dr;
   output                 update_dr;
   output                 tdo;
   output                 tdo_en;
   output [15:0]          tap_state;
   output                 extest;
   output                 samp_load;
   output [(width - 1):0] instructions;
   output                 sync_capture_en;
   output                 sync_update_dr;
 
   assign clock_dr = 0;
   assign shift_dr = 0;
   assign update_dr = 0;
   assign tdo = 0;
   assign tdo_en = 0;
   assign tap_state = 0;
   assign extest = 0;
   assign samp_load = 0;
   assign instructions = 0;
   assign sync_capture_en = 0;
   assign sync_update_dr = 0;
endmodule // CW_tap
