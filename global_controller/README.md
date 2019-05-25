# Global Controller source

## Global Controller ops by JTAG:
| Op                           | Opcode |config_data required   | config_addr required | Has output | Notes
| -----------------------------| :----: | :--------:            | :-------:            | :----:     | --------
|  NOP                         | 0 |                      |                      | 
|  CONFIG_WRITE                | 1 |:heavy_check_mark:   | :heavy_check_mark:   |            |        
|  CONFIG_READ                 | 2 |                     |  :heavy_check_mark:  | :heavy_check_mark: |           
|  WRITE_A050                  | 4 |                      |                      | :heavy_check_mark: | output A050 to JTAG. "Is the chip alive?"
|  WRITE_TST                   | 5 | :heavy_check_mark:   |                      |                    | A register we can r/w to. Doesn't do anything.
|  READ_TST                    | 6 |   |    | :heavy_check_mark: |          
|  GLOBAL_RESET                | 7 |:heavy_check_mark:  |   |   | Reset the CGRA fabric, but not the controller.
|  WRITE_STALL                 | 8 |:heavy_check_mark: |   |    |  Stall: N-bit register, where N=# of stall domains
|  READ_STALL                  | 9 |  |   | :heavy_check_mark: |       
|  ADVANCE_CLK                 | 10 |:heavy_check_mark:  | :heavy_check_mark:  |  |  Deassert stall domains asserted in config_addr for config_data cycles
|  READ_CLK_DOMAIN             | 11 |  |   |   :heavy_check_mark: |  Are we running the tiles on TCK or the faster system_clk? 0: TCK, 1: system_clk
|  SWITCH_CLK                  | 12 |:heavy_check_mark:  |   |     |    Switch to fast clk (config_data=1) or TCK (config_data=0)
|  WRITE_RW_DELAY_SEL          | 13 |:heavy_check_mark:  |    |     |  controls how long read/write as asserted for a config_read or config_write
|  READ_RW_DELAY_SEL           | 14 | |   |  :heavy_check_mark: |      
|  WRITE_CLK_SWITCH_DELAY_SEL  | 15 | :heavy_check_mark: |   |    |  Controls whether the clock is ungated on a rising edge (config_data=1) or a falling edge (config_data=0). Not actually modeled in functional model   
|  READ_CLK_SWITCH_DELAY_SEL   | 16 |  |   |  :heavy_check_mark: |
|  GLB_CONFIG_WRITE   | 17 | :heavy_check_mark: | :heavy_check_mark:  |  |
|  GLB_CONFIG_READ   | 18 |  | :heavy_check_mark: |  :heavy_check_mark: |
|  GLB_SRAM_CONFIG_WRITE   | 19 |:heavy_check_mark:  |  :heavy_check_mark: |  |
|  GLB_SRAM_CONFIG_READ   | 20 |  | :heavy_check_mark:  |  :heavy_check_mark: |
|  CGRA_CTRL_WRITE   | 21 |  :heavy_check_mark: |:heavy_check_mark: |  |
|  CGRA_START_READ   | 22 |  |  :heavy_check_mark: |  :heavy_check_mark: |


## Global Controller ops by AXI-Lite:
|         OP_CODE        | Addr[11:0] | Register Name                    |  Data  |        Write       |        Read        |                                  Notes                                  |
|:----------------------:|:----------:|----------------------------------|:------:|:------------------:|:------------------:|:-----------------------------------------------------------------------:|
|        TEST_REG        | 0x000 | test_reg                         | [31:0] | :heavy_check_mark: | :heavy_check_mark: |              Test register to check AXI-Lite is working.             |
|      GLOBAL_RESET      | 0x004 | global_reset                     | [31:0] | :heavy_check_mark: |                    |                 Apply reset. Clock cycle is set by data.                |
|          STALL         | 0x008 | cgra_start                       |  [3:0] | :heavy_check_mark: | :heavy_check_mark: |                                                                         |
| RD_DELAY_REG           | 0x00c | rd_delay_reg                     | [31:0] | :heavy_check_mark: | :heavy_check_mark: |     
| SOFT_RESET_DELAY             | 0x010 | delay register for soft reset                       | [31:0]    | :heavy_check_mark: | :heavy_check_mark: |                                                                    
| CGRA_START             | 0x014 | cgra_start                       | [0]    | :heavy_check_mark: | :heavy_check_mark: | Clear on cgra_done                                                      |
| CGRA_AUTO_RESTART      | 0x018 | cgra_auto_restart                | [0]    | :heavy_check_mark: | :heavy_check_mark: | Clear on restart                                                        |
|      CONFIG_START      | 0x01c | config_start                     |   [0]  | :heavy_check_mark: | :heavy_check_mark: |                           Clear on config_done                          |
|    INTERRUPT_ENABLE    | 0x020 | interrupt_enable_reg             |  [1:0] | :heavy_check_mark: | :heavy_check_mark: |            bit[0]: cgra_done_ier <br> bit[1]: config_done_ier           |
|    INTERRUPT_STATUS    | 0x024 | interrupt_status_reg             |  [1:0] | :heavy_check_mark: | :heavy_check_mark: | bit[0]: cgra_done_isr <br> bit[1]: config_done_isr <br> TOGGLE on Write |
|   CGRA_SOFT_RESET_EN   | 0x028 | cgra_soft_reset_en               |   [0]  | :heavy_check_mark: | :heavy_check_mark: |     
| CGRA CONFIG_ADDR     | 0x02c     | CGRA configuration address             | [31:0] | :heavy_check_mark: | :heavy_check_mark: |   
| CGRA CONFIG_DATA     | 0x030     | CGRA configuration data              | [31:0] | :heavy_check_mark: |:heavy_check_mark: | Config CGRA tiles with address stored in `CGRA_CONFIG_ADDR`
| GLB_SRAM CONFIG_ADDR     | 0x034     | GLB SRAM configuration address               | [31:0] | :heavy_check_mark: | :heavy_check_mark: |   
| GLB_SRAM CONFIG_DATA     | 0x038     | GLB SRAM configuration data    | [31:0] | :heavy_check_mark: | :heavy_check_mark:| Config global buffer SRAM with address stored in `GLB_SRAM_CONFIG_ADDR`  
| IO_CTRL     | if (addr[11:10] == 2'b01)    | IO controller configuration    | [31:0] | :heavy_check_mark: | :heavy_check_mark:| Config IO controllers inside the global buffer <br> addr[9:6] selects which IO_ctrl to config. <br> addr[5:2] selects which register to config. <br> register address mapping (0: mode, 1: start_addr, 2: num_word, 3: switch_mux, 4: done_delay)
| CFG_CTRL     | if (addr[11:10] == 2'b10)    | Parallel config controller configuration    | [31:0] | :heavy_check_mark: | :heavy_check_mark:| Config parallel config controllers inside the global buffer  <br> addr[9:6] selects which CFG_ctrl to config. <br> addr[5:2] selects which register to config. <br> register address mapping (0: start_addr, 1: num_bitstream, 2: switch_mux)

## Using the functional Model:
An example:
```
gc_inst = gc()
res = gc_inst(op=GCOp.CONFIG_WRITE, addr=random_addr, data=random_data)
```

When calling the global controller functional model, you can provide 3 kwargs: 
- op (GCOp)
- addr
- data

Op is required, but data, and addr may or may not be required, depending on the op (see the table of ops for more info).
Calling the functional model.

This returns the global controller object which you can probe to see the output sequence that resulted from the op.

Here's a list of the attributes you can probe:
- config_addr_out
- config_data_out
- read
- config_data_to_jtag
- rw_delay_sel
- clk_switch_delay_sel
- TST
- stall
- clk_sel

Each of these attributes represents either an output or internal register of the GC. Because the responses to many of the global controller ops span multiple clock cycles, each of these attributes is a Python list, where each element of the list corresponds to the value of that register in a single clock cycle. If an op doesn't affect a specific attribute, it is left as a list of length 1. The sole element of this list is the value of this signal for the duration of the op.



### Things That Aren't Modeled (yet):
- For clock switching, you just write to a clock select register. There are no clock inputs or outputs in the functional model.
- Clock switch delay select. You can select whether at the end of a clock switch, the clock is ungated on a rising or falling edge in the actual hardware. Again, in the functional model, this is just a 1 bit register you can read from/write to.

## CGRA control
- Once `AXI` or `JTAG` writes `1` to `cgra_start` register, `cgra_start_pulse` is generated and sent to `address_generator` and `interconnect`.
- Once application is done, `cgra_done_pulse` is generated from `interconnect`. This will clear `cgra_start` register and set the `cgra_done_isr` interrupt status register. (only if `cgra_done ier` interrupt enable register is set to high)
- `AXI` or `JTAG` is able to TOGGLE the `cgra_done_isr`. 
```
cgra_done_isr[0] <= cgra_done_isr[0] ^ WR_DATA[0];
```
- This technique is widely used in controlling interrupt status registers. The reason to TOGGLE interrupt status register is that if there are multiple interrupt status registers, processor need to read all interrupt status registers to find which has caused interrupt, and processor would just write the data back to interrupt status register to clear all interrupt.
