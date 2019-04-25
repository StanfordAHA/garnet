# Tapeout checklist

## Timing (source: Primetime output)
- [ ] Primetime hold margin across all scenarios >= 0.2 ns
- [ ] Max clock frequency (TC 0.8 V) > 40 MHz, (TC 1.2 V) > 80 MHz
- [ ] JTAG clock always > 20 MHz

## Functional verification (source: pytest log)
- [ ] CGRA + GB unit test suite - RTL vs functional model
    - [ ] PE
    - [ ] Memory
    - [ ] SB
    - [ ] CB
    - [ ] Global Controller
    - [ ] Global Buffer
- [ ] CGRA + GB integration tests using apps (with SoC stub)
- [ ] SoC unit test suite
- [ ] SoC integration tests (with CGRA + GB stub)
- [ ] CGRA + GB + SoC integration tests (with FPGA stub)
- [ ] CGRA + GB + SoC + FPGA tests
- [ ] Gate level simulation - tests passing
- [ ] Gate level simulation - no timing violations
- [ ] FPGA demo
- [ ] Formal verification - RTL vs gates
- [ ] Formal verification - Configured CGRA vs CoreIR DAG
- [ ] Power domain aware RTL simulation
- [ ] Power domain aware gate level simulation

## Physical verification
- [ ] DRC (primiary) 

## Sanity checks on tool generated reports

## Peripheral issues

## Waiver requests
