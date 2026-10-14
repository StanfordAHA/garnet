#!/bin/bash
# Record the two versions of conv_3_3's line buffer as app bundles for
# mflowgen/cgra_app_power.py (mflowgen/CLAUDE.md "conv_3_3 A/B"):
#   A  today's dense RV mapping: the newest-row tap is a wire from the input
#      IO, the SRAM readers stream the whole frame, the GLB store drops the
#      first two rows/columns ("eat at the output")
#   B  the newest-row tap goes through the MEM's filter path, whose item filter
#      drops rows 0-1 ("eat up front"; hooks/conv_3_3_eat_rows_up_front.py)
#
# usage: conv_3_3_ab_bundles.sh <bundle root> [config]
#   config  a sweep_specs.py config name with a filter path; default
#           fw4_dw16_sc8192_sp_in2_out2_vc2_ff8_rv (spec set filter_fifo: the
#           filter path as an 8-deep FIFO)
# -> <bundle root>/A/<config>, <bundle root>/B/<config>, then on the build machine:
#   ./mflowgen/cgra_app_power.py --variants A=<root>/A,B=<root>/B --out-dir <dir>
#
# Runs where the spec toolchain lives (an aha tree, $AHA_DIR, default /aha),
# with xrun on PATH and aha's venv active. Each variant runs in its own
# private aha tree under <bundle root>/trees (symlinks to $AHA_DIR's entries,
# except garnet: a clone of this garnet checkout's HEAD), because garnet.py
# --verilog rewrites $GARNET_HOME's GLB headers; and on its own app copy,
# Halide-to-Hardware/apps/hardware_benchmarks/cgra_ab_<V>/conv_3_3.
# Bundles are recorded with --cgra-tiles (route-through + idle tiles).
set -euo pipefail
root=$(readlink -f "${1:?usage: conv_3_3_ab_bundles.sh <bundle root> [config]}")
config=${2:-fw4_dw16_sc8192_sp_in2_out2_vc2_ff8_rv}
aha=$(readlink -f "${AHA_DIR:-/aha}")
here=$(cd "$(dirname "$0")" && pwd)
garnet=$(cd "$here/../../.." && pwd)
apps="$aha/Halide-to-Hardware/apps/hardware_benchmarks"
src="$apps/tests/conv_3_3"
command -v xrun > /dev/null || { echo "*** xrun not on PATH (module load xcelium)"; exit 1; }
mkdir -p "$root/trees"

for V in A B; do
  t="$root/trees/$V"
  if [ ! -d "$t/garnet" ]; then
    mkdir -p "$t"
    for e in "$aha"/* "$aha"/.[a-z]*; do
      n=$(basename "$e"); [ "$n" = garnet ] || [ -e "$t/$n" ] || ln -s "$e" "$t/$n"
    done
    git clone -q "$garnet" "$t/garnet"
  fi
  app="$apps/cgra_ab_$V/conv_3_3"
  if [ ! -d "$app" ]; then
    mkdir -p "$app"
    (cd "$src" && git ls-files . | while read -r f; do mkdir -p "$app/$(dirname "$f")"; cp "$f" "$app/$f"; done)
  fi
done

run() {  # run <V> [gen_app_bundle args]
  local V=$1; shift
  python3 "$root/trees/$V/garnet/mflowgen/common/application/gen_app_bundle.py" \
    --config "$config" --bundle-dir "$root/$V" --aha-dir "$root/trees/$V" \
    --app "cgra_ab_$V/conv_3_3" --cgra-tiles "$@" > "$root/$V.log" 2>&1
}
run A & pa=$!
METAMAPPER_MEM_PORTS=3 run B --pre-pnr-hook "$here/hooks/conv_3_3_eat_rows_up_front.py" & pb=$!
rc=0
wait $pa || { echo "*** A failed: $root/A.log"; rc=1; }
wait $pb || { echo "*** B failed: $root/B.log"; rc=1; }
[ $rc = 0 ] && echo "bundles: $root/A/$config $root/B/$config"
exit $rc
