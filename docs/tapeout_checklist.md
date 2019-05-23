# Tapeout checklist

## Timing (source: Primetime, Innovus)
- [ ] Primetime hold margin across all scenarios >= xx ns
- [ ] Max clock frequency (TC 0.8 V) > xx MHz, (TC 1.2 V) > xx MHz
- [ ] JTAG clock always > xx MHz
- [ ] Report all static timing analysis overrides (false paths, multicycle paths), make sure they are okay
- [ ] Static timing overrides in gate level simulation verified
- [ ] Primetime infers clock gating checks
- [ ] Clock tree report - reasonable tree depth, insertion delay, skew

## Physical verification (source: Calibre log)
- [ ] DRC (primary) - no errors except waived
- [ ] DRC (antenna) - no errors
- [ ] DRC (wirebond) - no errors except waived
- [ ] ERC - no errors except waived
- [ ] LVS - correct
- [ ] All of the above pass after dummy fill

## Power domain checks
- [ ] PG nets verified
- [ ] Clock tree multi-voltage safety
- [ ] check_mv_design (equivalent Innovus command) clean
- [ ] Decoupling
- [ ] Worst power + group IR drop in Primerail report (static) < xx mV

## Other sanity checks
- [ ] Bond pad labels match pinout
- [ ] All memory stubs replaced by SRAM macros

## Functional verification (source: pytest log)
### RTL functional verification
- [ ] CGRA + GB unit test suite - RTL vs functional model
- [ ] CGRA + GB integration tests using apps (with SoC stub)
- [ ] SoC unit test suite
- [ ] SoC integration tests (with CGRA + GB stub)
- [ ] CGRA + GB + SoC integration tests (with FPGA stub)
- [ ] CGRA + GB + SoC + FPGA tests (after tapeout)
### Gate level functional verification
- [ ] All of the above tests pass at gate level with no timing violations
### Power domain aware RTL/gate level simulation/formal checking
### Formal verification
- [ ] RTL vs gates
- [ ] Configured CGRA vs CoreIR DAG

## Unit test coverage
- [ ] PE
    - [ ] All ops with randomized inputs
    - [ ] Directed tests on ops for corner cases
    - [ ] Multi-tile ops
        - [ ] div
        - [ ] exp
        - [ ] power
        - [ ] ln
        - [ ] sin
        - [ ] int to bfloat?
        - [ ] bfloat to int?
- [ ] Memory
    - [ ] FIFO
    - [ ] Linebuffer
        - [ ] With downsample
        - [ ] With upsample
    - [ ] SRAM/LUT for multi-tile ops
    - [ ] Double buffer
        - [ ] With stride
- [ ] Global buffer 
    - [ ] FIFO
    - [ ] Double buffer
    - [ ] SRAM
- [ ] Global controller
- [ ] Interconnect
- [ ] SoC

## CGRA integration test coverage
- [ ] Gate level full chip reset
    - [ ] With power switches
- [ ] Read and write all registers and memories through JTAG
- [ ] Apps
    - [ ] Pointwise
    - [ ] 1x1, 3x3, 5x5, 7x7 conv
        - [ ] With floating point
        - [ ] With stride
    - [ ] Harris
    - [ ] Camera pipe (tests SRAM mode in memory tile)
    - [ ] Multi-channel conv (tests double buffer at 1st and 2nd level memory)
    - [ ] Multi-rate conv
    - [ ] Cascade

# SoC integration test coverage
## Tests
- [ ] Boot load using JTAG
- [ ] Boot SoC
- [ ] Interrupts
- [ ] CGRA memory (at different async frequencies)
- [ ] CGRA configuration space registers (at different frequencies)
- [ ] Hello
- [ ] Uart
- [ ] Timer
- [ ] Interconnect
- [ ] DMA (at different frequencies)
- [ ] Application tests via API
  - [ ] Pointwise
  - [ ] Camera pipe
  
## Environments

SoC/CGRA stub/TLX stub

SoC/CGRA/TLX stub

SoC/CGRA/TLX (Chip)

SoC stub/FPGA 

SoC/CGRA/TLX/FPGA

All tests must pass on all environments

## Waiver requests

### Gate level simulation
Timing violations reported by simulator: The simulation includes power state changes that set the output of all cells within a power domain to X when its supply is disables. Because the simlator treats X-to-0 and X-to-1 transitions as edges, it is possible for these transistions to trigger $setuphold checks in the standard cell library when the supply is enabled. Only violations pertaining to power state changes, which do not affect functionality, can be ignored. 
