# Global Controller source

## Global Controller ops:
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
|  CGRA_START_WRITE   | 21 |  :heavy_check_mark: |  |   |
|  CGRA_START_READ   | 22 |  |   |  :heavy_check_mark: |
|  CONFIG_START_WRITE | 23 | :heavy_check_mark: |  |  |
|  CONFIG_START_READ | 24 |  |   |  :heavy_check_mark: |
|  WRITE_IER   | 25 | :heavy_check_mark:  |  |   |
|  READ_IER   | 26 |  |   |  :heavy_check_mark: |
|  WRITE_ISR   | 27 | :heavy_check_mark:  |  |   |
|  READ_ISR   | 28 |  |   |  :heavy_check_mark: |


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
