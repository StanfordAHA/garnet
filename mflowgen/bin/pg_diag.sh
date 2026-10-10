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
#         license), PG_DIAG_TOP=Tile_MemCore
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
  echo "START $name ($(date +%H:%M:%S))"
  ( cd "$d" && PG_DIAG_CKPT=$(readlink -f "$ck") PG_DIAG_TOP=${PG_DIAG_TOP:-Tile_MemCore} \
      innovus -64 -nowin -overwrite -files "$tcl" -log innovus.log < /dev/null > innovus.stdout 2>&1 )
  echo "DONE  $name ($(date +%H:%M:%S)): $(head -1 "$d/opens.txt" 2>/dev/null || echo 'no opens.txt, see innovus.log')"
}

for ws in "$@"; do
  while [ "$(jobs -rp | wc -l)" -ge "$jobs" ]; do sleep 5; done
  run_one "$ws" &
done
wait

tar czf "$out.tgz" -C "$(dirname "$out")" --exclude='innovus_temp_*' --exclude='*.logv' "$(basename "$out")"
echo "Reports: $out  ->  $out.tgz ($(du -h "$out.tgz" | cut -f1))"
