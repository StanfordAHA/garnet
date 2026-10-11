#!/usr/bin/env bash
#=============================================================================
# pg_diag.sh -- read-only power-grid / DRC diagnosis of finished PnR builds
#=============================================================================
# For each mflowgen workspace given, restores its signoff checkpoint
# (<ws>/<N>-cadence-innovus-signoff/checkpoints/design.checkpoint/save.enc.dat)
# in Innovus from <out>/<workspace name>/, runs pg_diag.tcl there and packs
# the text reports into <out>.tgz. Nothing is written into the workspaces:
# the design is never saved, and the in-memory via trials are discarded.
#
# Usage:  mflowgen/bin/pg_diag.sh <out dir> <workspace>...
#   env:  JOBS=2 (Innovus runs at once; each takes an invs + invs_20nm
#         license), PG_DIAG_TOP=Tile_MemCore, PG_DIAG_TRIALS="vias" (any of
#         trim pins vias, applied in order), PG_DIAG_DRC=1 (0 skips the
#         full-design verify_drc)
#
# What it answers (VSS opens in garnet open issue garnet/pnr-drc-vss-opens):
# which wires/vias/cells sit in each verifyConnectivity open, whether std
# cells lose their ground there, what verify_drc finds beyond its default
# 1000-violation cap (blockage artifacts vs real), and whether re-dropping
# M1..M3 power vias closes the opens (and what DRCs forcing them costs).

set -u
if [ $# -lt 2 ]; then
  sed -n '2,20p' "$0"; exit 2
fi
out=$(mkdir -p "$1" && cd "$1" && pwd); shift
tcl=$(cd "$(dirname "$0")" && pwd)/pg_diag.tcl
jobs=${JOBS:-2}
command -v innovus >/dev/null || { echo "innovus not on PATH"; exit 1; }

run_one() {
  local ws=$1 name ck d
  name=$(basename "$ws")
  ck=$(ls -d "$ws"/*-cadence-innovus-signoff/checkpoints/design.checkpoint/save.enc.dat 2>/dev/null | head -1)
  if [ -z "$ck" ]; then echo "SKIP $name: no signoff checkpoint under $ws"; return; fi
  d="$out/$name"; mkdir -p "$d"
  # how the ADK places endcaps / well taps (adk.tcl of the workspace's adk step)
  local adk
  adk=$(ls "$ws"/*-adk/outputs/adk/adk.tcl 2>/dev/null | head -1)
  if [ -n "$adk" ]; then
    { echo "# $adk"; grep -n -i -E "END_CAP|WELL_TAP|ENDCAP|COLCAP|TAPCELL" "$adk"
      for p in adk_set_end_cap_mode adk_add_end_caps adk_set_well_tap_mode adk_add_well_taps; do
        awk -v p="$p" '$1=="proc" && $2==p {f=1} f {print} f && /^}/ {f=0}' "$adk"
      done; } > "$d/adk_endcaps.txt" 2>&1
  fi
  echo "START $name ($(date +%H:%M:%S))"
  ( cd "$d" && PG_DIAG_CKPT=$(readlink -f "$ck") PG_DIAG_TOP=${PG_DIAG_TOP:-Tile_MemCore} \
      PG_DIAG_TRIALS=${PG_DIAG_TRIALS:-vias} PG_DIAG_DRC=${PG_DIAG_DRC:-1} \
      innovus -64 -nowin -overwrite -files "$tcl" -log innovus.log < /dev/null > innovus.stdout 2>&1 )
  echo "DONE  $name ($(date +%H:%M:%S)): $(cat "$d/opens_class.txt" 2>/dev/null || head -1 "$d/opens.txt" 2>/dev/null || echo 'no opens.txt, see innovus.log')"
}

for ws in "$@"; do
  while [ "$(jobs -rp | wc -l)" -ge "$jobs" ]; do sleep 5; done
  run_one "$ws" &
done
wait

tar czf "$out.tgz" -C "$(dirname "$out")" --exclude='innovus_temp_*' --exclude='*.logv' "$(basename "$out")"
echo "Reports: $out  ->  $out.tgz ($(du -h "$out.tgz" | cut -f1))"
