# Global Controller Checklist

## CGRA control - both by SoC & JTAG
- [:heavy_check_mark:] CGRA start/done/auto_start signal tests
- [:heavy_check_mark:] Fast reconfiguration start/done signal tests
- [:heavy_check_mark:] Interrupt signal tests (Set/Clear interrupt)

## OPCODE tests
| OPCODE                | JTAG             | AXI4-Lite |
|-----------------------|------------------|-----------|
| NOP                   |:heavy_check_mark:|:heavy_check_mark:|
| write_config          |:heavy_check_mark:|:heavy_check_mark:|
| read_config           |:heavy_check_mark:|:heavy_check_mark:|
| write_A050            |:heavy_check_mark:|N/A|
| write_TST             |:heavy_check_mark:|:heavy_check_mark:|
| read_TST              |:heavy_check_mark:|:heavy_check_mark:|
| global_reset          |:heavy_check_mark:|:heavy_check_mark:|
| write_stall           |:heavy_check_mark:|:heavy_check_mark:|
| read_stall            |:heavy_check_mark:|:heavy_check_mark:|
| advance_clk           |:heavy_check_mark:|N/A|
| read_clk_domain       |:heavy_check_mark:|N/A|
| switch_clk            |:heavy_check_mark:|N/A|
| wr_rd_delay_reg       |:heavy_check_mark:|:heavy_check_mark:|
| rd_rd_delay_reg       |:heavy_check_mark:|:heavy_check_mark:|
| wr_delay_sel_reg      |:heavy_check_mark:|N/A|
| rd_delay_sel_reg      |:heavy_check_mark:|N/A|
| glb_write_config      |:heavy_check_mark:|:heavy_check_mark:|
| glb_read_config       |:heavy_check_mark:|:heavy_check_mark:|
| glb_sram_write_config |:heavy_check_mark:|:heavy_check_mark:|
| glb_sram_read_config  |:heavy_check_mark:|:heavy_check_mark:|
| cgra_ctrl_write       |:heavy_check_mark:|:heavy_check_mark:|
| cgra_ctrl_read        |:heavy_check_mark:|:heavy_check_mark:|
