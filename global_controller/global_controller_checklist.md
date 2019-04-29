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
