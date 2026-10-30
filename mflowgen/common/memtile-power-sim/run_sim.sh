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

# PnR level (Tile_MemCore wires the signoff design.sdf in): simulate the
# signoff netlist with its SDF, like the app replays (common/testbench,
# cadence-xcelium-sim). Without it the post-CTS netlist ran on the cell
# models' specify delays only, and a clock-tree race left one RV output port
# of 2 of 37 thesis_dse tiles silent (garnet/pnr-power-sim-no-sdf-race).
# The testbench then drives each input when the tile SDC says it arrives
# (Tile_MemCore/constraints/common.tcl: i_delay, pt_i_delay; same env
# overrides), since PnR fixed hold for those times, and timing checks stay on
# for the negative-check delayed signals with -nonotifier (a violation is
# reported, it doesn't turn flops X).
sdf=""
tchk_x="-notimingchecks"
tchk_v="+notimingcheck +nospecify"
if [ -f inputs/design.sdf ]; then
    SDC_I_DELAY_FRAC=0.2
    SDC_PT_I_DELAY_NS=0.700
    i_delay=$(awk -v v="${TILE_I_DELAY_NS:-}" -v f=$SDC_I_DELAY_FRAC -v t="$clock_period" \
        'BEGIN { print (v != "" ? v + 0 : f * t) }')
    pt_i_delay=$(awk -v v="${PT_I_DELAY_FRAC:-}" -v d=$SDC_PT_I_DELAY_NS -v t="$clock_period" \
        'BEGIN { print (v != "" ? v * t : d + 0) }')
    defs+=" +define+IN_DELAY=$i_delay +define+PT_IN_DELAY=$pt_i_delay"
    echo "memtile power test: SDF inputs/design.sdf, inputs driven at i_delay $i_delay / pt_i_delay $pt_i_delay ns"
    cat > sdf_cmd.cmd <<EOF
SDF_FILE = "inputs/design.sdf",
SCOPE = testbench.dut,
LOG_FILE = "logs/sdf.log",
MTM_CONTROL = "MAXIMUM";
EOF
    sdf="-sdf_cmd_file sdf_cmd.cmd -negdelay"
    tchk_x="-nonotifier"
    tchk_v="-sdf max:testbench.dut:inputs/design.sdf +neg_tchk +no_notifier"
fi

echo "memtile power test: variant=$variant tool=$tool"
if [ "$tool" == "VCS" ]; then
    (set -x; vcs -full64 -sverilog -timescale=1ns/1ps -top testbench +vcs+lic+wait \
        $tchk_v $defs $files -l logs/compile.log -o simv)
    (set -x; ./simv -l logs/sim.log)
else
    (set -x; xrun -64bit -sv -timescale 1ns/1ps -access +r $tchk_x -licqueue -ALLOWREDEFINITION \
        -top testbench $defs $sdf +define+MEMTILE_SAIF_TCL -input cmd.tcl $files -l logs/sim.log)
fi

grep "MEMTILE_POWER_TEST" logs/sim.log || true
# A test that did not do what it is named for must not produce a power number.
if ! grep -q "MEMTILE_POWER_TEST $variant PASS" logs/sim.log; then
    echo "*** ERROR: memtile power test '$variant' did not PASS (see logs/sim.log)" >&2
    exit 1
fi
mv run.saif outputs/run.saif
