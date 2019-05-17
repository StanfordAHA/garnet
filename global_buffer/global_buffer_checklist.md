# Global Buffer Checklist

## Global Buffer Banks
- [ ] Config all SRAMs using JTAG (read/write)
- [ ] SoC write/read to Global Buffer (Latency due to pipeline)
- [ ] Partial write support by JTAG configuration / SRAM mode

## Address Generator + Data Interconnection
- [ ] Config all registers in address generator and interconnection
- [x] FIFO mode tests (start address not block aligned, multiple input/output streams run concurrently)
- [ ] SRAM mode tests (partial write, read latency)
- [ ] Interconnection tests (Address generator access to flexible number of banks)
- [ ] Stall signal (Does not write/read when stalled)
- [x] App start/done signal tests
- [x] Auto start mode tests (No need to wait for host for restart)

## Fast Reconfiguration
- [ ] Config all registers in fast reconfiguration controller
- [ ] Interconnection tests
- [ ] Config start/done signal tests
- [ ] Parallel config tests
