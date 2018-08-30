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

## Using the functional Model:
