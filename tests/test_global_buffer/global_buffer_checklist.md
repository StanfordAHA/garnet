# Global Buffer Checklist

## Global Buffer Banks
- [x] Config all SRAMs using JTAG (read/write) 
- https://github.com/StanfordAHA/garnet/blob/78972a668ccd0b498dca10860850008bfd3a86e8/tests/test_global_buffer/verilator/test_global_buffer_int.cpp#L826
- [x] SoC write/read to Global Buffer (Latency due to pipeline) 
- https://github.com/StanfordAHA/garnet/blob/78972a668ccd0b498dca10860850008bfd3a86e8/tests/test_global_buffer/verilator/test_global_buffer_int.cpp#L858

## IO controller + Address Generator
- [x] Config all registers in IO controller 
- https://github.com/StanfordAHA/garnet/blob/78972a668ccd0b498dca10860850008bfd3a86e8/tests/test_global_buffer/verilator/test_io_controller.cpp#L505
- [x] FIFO mode tests (start address not block aligned, multiple input/output streams run concurrently) 
- https://github.com/StanfordAHA/garnet/blob/78972a668ccd0b498dca10860850008bfd3a86e8/tests/test_global_buffer/verilator/test_io_controller.cpp#L524
- https://github.com/StanfordAHA/garnet/blob/78972a668ccd0b498dca10860850008bfd3a86e8/tests/test_global_buffer/verilator/test_io_controller.cpp#L557
- [x] SRAM mode tests (partial write, read latency) 
- https://github.com/StanfordAHA/garnet/blob/78972a668ccd0b498dca10860850008bfd3a86e8/tests/test_global_buffer/verilator/test_global_buffer_int.cpp#L920

## Fast Reconfiguration
- [x] Config all registers in fast reconfiguration controller 
-  https://github.com/StanfordAHA/garnet/blob/78972a668ccd0b498dca10860850008bfd3a86e8/tests/test_global_buffer/verilator/test_cfg_controller.cpp#L424
- [x] Parallel config tests 
- https://github.com/StanfordAHA/garnet/blob/78972a668ccd0b498dca10860850008bfd3a86e8/tests/test_global_buffer/verilator/test_cfg_controller.cpp#L445
- https://github.com/StanfordAHA/garnet/blob/78972a668ccd0b498dca10860850008bfd3a86e8/tests/test_global_buffer/verilator/test_cfg_controller.cpp#L475
- [x] Jtag configuration still works
- https://github.com/StanfordAHA/garnet/blob/78972a668ccd0b498dca10860850008bfd3a86e8/tests/test_global_buffer/verilator/test_cfg_controller.cpp#L516
