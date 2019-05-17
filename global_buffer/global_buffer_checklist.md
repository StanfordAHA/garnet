# Global Buffer Checklist

## Global Buffer Banks
- [ ] Config all SRAMs using JTAG (read/write)
- [ ] SoC write/read to Global Buffer (Latency due to pipeline)
- [ ] Partial write support

## Address Generator + Data Interconnection
- [x] Config all registers in address generator and interconnection
- [x] FIFO mode tests (start address not block aligned, multiple input/output streams run concurrently)
- [ ] SRAM mode tests (partial write, read latency)
- [x] Interconnection tests (Address generator access to flexible number of banks)
- [x] Stall signal (Does not write/read when stalled)
- [x] App start/done signal tests
- [x] Auto start mode tests (No need to wait for host for restart)

## Fast Reconfiguration
- [x] Config all registers in fast reconfiguration controller
- [x] Interconnection tests
- [x] Config start/done signal tests
- [x] Parallel config tests
