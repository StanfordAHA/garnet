# Global Controller Checklist

## SoC ports
- [ ] Write all global buffer configuration registers
- [ ] Write/read CGRA-control configuration registers

## JTAG ports
- [ ] Write/Read all CGRA configuration registers
- [ ] Write/Read all global buffer configuration registers
- [ ] Write/Read all global buffer SRAM
- [ ] Write/Read all CGRA configuration registers

## CGRA control - both by SoC & JTAG
- [:heavy_check_mark:] CGRA start/done/auto_start signal tests
- [:heavy_check_mark:] Fast reconfiguration start/done signal tests
- [ ] Interrupt signal tests (Set/Clear interrupt)

## OPCODE tests
| OPCODE                | JTAG             | AXI4-Lite |
|-----------------------|------------------|-----------|
| NOP                   |:heavy_check_mark:|:heavy_check_mark:|
| write_config          |:heavy_check_mark:|           |
| read_config           |:heavy_check_mark:|           |
| write_A050            |:heavy_check_mark:      |           |
| write_TST             |:heavy_check_mark:      |           |
| read_TST              |:heavy_check_mark:       |           |
| global_reset          |:heavy_check_mark:       |           |
| write_stall           |:heavy_check_mark:      |           |
| read_stall            |:heavy_check_mark:      |           |
| advance_clk           |:heavy_check_mark:      |           |
| read_clk_domain       |:heavy_check_mark:       |           |
| switch_clk            |:heavy_check_mark:       |           |
| wr_rd_delay_reg       |:heavy_check_mark:      |           |
| rd_rd_delay_reg       |:heavy_check_mark:      |           |
| wr_delay_sel_reg      |:heavy_check_mark:       |           |
| rd_delay_sel_reg      |:heavy_check_mark:       |           |
| glb_write_config      |:heavy_check_mark:      |           |
| glb_read_config       |:heavy_check_mark:     |           |
| glb_sram_write_config |:heavy_check_mark:      |           |
| glb_sram_read_config  |:heavy_check_mark:       |           |
| cgra_ctrl_write       |:heavy_check_mark:      |           |
| cgra_ctrl_read        |:heavy_check_mark:      |           |
