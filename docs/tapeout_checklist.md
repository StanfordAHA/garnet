# Tapeout checklist

## Timing (source: Primetime output)
- [ ] Primetime hold margin across all scenarios >= xx ns
- [ ] Max clock frequency (TC 0.8 V) > xx MHz, (TC 1.2 V) > xx MHz
- [ ] JTAG clock always > xx MHz

## Functional verification (source: pytest log)
- [ ] CGRA + GB unit test suite - RTL vs functional model
- [ ] CGRA + GB integration tests using apps (with SoC stub)
- [ ] SoC unit test suite
- [ ] SoC integration tests (with CGRA + GB stub)
- [ ] CGRA + GB + SoC integration tests (with FPGA stub)
- [ ] CGRA + GB + SoC + FPGA tests
- [ ] Gate level simulation - tests passing
- [ ] Gate level simulation - no timing violations
- [ ] Formal verification - RTL vs gates
- [ ] Formal verification - Configured CGRA vs CoreIR DAG
- [ ] Power domain aware RTL simulation
- [ ] Power domain aware gate level simulation

## Physical verification
- [ ] DRC (primary) - no errors except waived
- [ ] DRC (antenna) - no errors
- [ ] DRC (wirebond) - no errors except waived
- [ ] ERC - no errors except waived
- [ ] LVS - correct
- [ ] All of the above pass after dummy fill

## Sanity checks on tool generated reports
- [ ] DRC and LVS from within Innovus
- [ ] PG nets verified
- [ ] Clock tree multi-voltage safety
- [ ] check_mv_design (equivalent Innovus command) clean
- [ ] Clock tree report - reasonable tree depth, insertion delay, skew
- [ ] Decoupling
- [ ] Worst power + group IR drop in Primerail report (static) < xx mV
- [ ] Primetime results at nominal voltage similar to other results (setup and hold margin)
- [ ] Report all static timing analysis overrides (false paths, multicycle paths), make sure they are okay
- [ ] Static timing overrides in gate level simulation verified
- [ ] Primetime infers clock gating checks
- [ ] Bond pad labels match pinout

## Peripheral issues
- [ ] All memory stubs replaced by SRAM macros

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
- [ ] SoC??

## Integration test coverage
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

## Waiver requests

### Gate level simulation
Timing violations reported by simulator: The simulation includes power state changes that set the output of all cells within a power domain to X when its supply is disables. Because the simlator treats X-to-0 and X-to-1 transitions as edges, it is possible for these transistions to trigger $setuphold checks in the standard cell library when the supply is enabled. Only violations pertaining to power state changes, which do not affect functionality, can be ignored. 
