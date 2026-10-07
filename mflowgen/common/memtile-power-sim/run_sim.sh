#!/bin/bash
# Run one memtile power test (testbench.sv from memtile-power-test-gen) on the
# netlist in inputs/design.v and leave its switching activity in
# outputs/run.saif. Activity covers the measurement window only (config load
# excluded): VCS via the testbench's $toggle_* tasks, Xcelium via cmd.tcl's
# dumpsaif between the testbench's two $stops. The testbench also prints
#   MEMTILE_POWER_TEST <variant> PASS|FAIL
# from its own output-activity check; the step postcondition gates on PASS.
set -e
mkdir -p outputs logs
rm -f run.saif

files=""
# Standard-cell models for gate-level netlists: every ADK Verilog model (as
# lake pd/thesis's gf12 gate-level sims do, so multi-Vt cells resolve), minus
# the power-aware *pwr* variants (the netlist has no supply pins). An RTL
# design.v needs none.
for f in inputs/adk/*.v; do
    case "$f" in *pwr*) continue ;; esac
    if [ -f "$f" ]; then files+=" $f"; fi
done
files+=" inputs/design.v"
if [ -f inputs/sram.v ]; then files+=" inputs/sram.v"; fi
files+=" inputs/testbench.sv"
defs="+define+CLK_PERIOD=$clock_period"

echo "memtile power test: variant=$variant tool=$tool"
if [ "$tool" == "VCS" ]; then
    (set -x; vcs -full64 -sverilog -timescale=1ns/1ps -top testbench +vcs+lic+wait \
        +notimingcheck +nospecify $defs $files -l logs/compile.log -o simv)
    (set -x; ./simv -l logs/sim.log)
else
    (set -x; xrun -64bit -sv -timescale 1ns/1ps -access +r -notimingchecks -licqueue -ALLOWREDEFINITION \
        -top testbench $defs +define+MEMTILE_SAIF_TCL -input cmd.tcl $files -l logs/sim.log)
fi

grep "MEMTILE_POWER_TEST" logs/sim.log || true
# A test that did not do what it is named for must not produce a power number.
if ! grep -q "MEMTILE_POWER_TEST $variant PASS" logs/sim.log; then
    echo "*** ERROR: memtile power test '$variant' did not PASS (see logs/sim.log)" >&2
    exit 1
fi
mv run.saif outputs/run.saif
