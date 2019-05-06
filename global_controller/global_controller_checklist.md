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
- [ ] CGRA start/done/auto_start signal tests
- [ ] Fast reconfiguration start/done signal tests
- [ ] Interrupt signal tests (Set/Clear interrupt)

## OPCODE tests
| OPCODE                | JTAG | AXI4-Lite |
|-----------------------|------|-----------|
| NOP                   |      |           |
| write_config          |      |           |
| read_config           |      |           |
| write_A050            |      |           |
| write_TST             |      |           |
| read_TST              |      |           |
| global_reset          |      |           |
| write_stall           |      |           |
| read_stall            |      |           |
| advance_clk           |      |           |
| read_clk_domain       |      |           |
| switch_clk            |      |           |
| wr_rd_delay_reg       |      |           |
| rd_rd_delay_reg       |      |           |
| wr_delay_sel_reg      |      |           |
| rd_delay_sel_reg      |      |           |
| glb_write_config      |      |           |
| glb_read_config       |      |           |
| glb_sram_write_config |      |           |
| glb_sram_read_config  |      |           |
| cgra_ctrl_write       |      |           |
| cgra_ctrl_read        |      |           |
