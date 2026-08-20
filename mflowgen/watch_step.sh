#!/usr/bin/env bash
#=============================================================================
# watch_step.sh -- live-follow the currently-running mflowgen step's log
#=============================================================================
# mflowgen runs each step in its own build subdir "NN-stepname/" and tees that
# step's console output to "NN-stepname/mflowgen-run.log". A step is *running*
# when its dir has a ".time_start" but no ".time_end" (mflowgen removes
# .time_end at start and writes it at finish).
#
# This script figures out which step is live and streams its log, and it
# automatically hops to the next step when the current one finishes -- so you
# never have to hunt for "which NN-dir is running now". It also keeps a stable
# symlink  <build_dir>/current-step.log  pointing at that live log, so you can
# alternatively just:  tail -F <build_dir>/current-step.log
#
# Usage:
#   ./watch_step.sh [build_dir]              # stream + follow step transitions
#   ./watch_step.sh --symlink-only [dir]     # only maintain current-step.log
#   ./watch_step.sh --list [dir]             # print step states and exit
#
#   build_dir defaults to $PWD. For the spec sweep it is the per-config dir,
#   e.g.  sweep_out/tile_memcore_pnr/fw1_dw16_sc4096_sp_in1_out1
#
# No dependencies beyond bash + GNU coreutils (find/stat/ln/tail).
#=============================================================================
set -u

POLL=2                       # seconds between checks
LINK_NAME="current-step.log" # symlink maintained in build_dir
RUN_LOG="mflowgen-run.log"   # per-step live log written by mflowgen

mode="stream"
case "${1:-}" in
  --symlink-only) mode="symlink"; shift ;;
  --list)         mode="list";    shift ;;
  -h|--help)      grep '^#' "$0" | sed 's/^#//' ; exit 0 ;;
esac

BUILD="${1:-$PWD}"
BUILD="${BUILD%/}"
if [ ! -d "$BUILD" ]; then
  echo "watch_step: build dir not found: $BUILD" >&2
  exit 1
fi

# Print epoch mtime of a file, or 0 if missing.
mtime() { stat -c %Y "$1" 2>/dev/null || echo 0; }

# Echo the basename of the step dir to follow, or empty if none found.
# Preference:
#   1) a running step (.time_start present, .time_end absent) -- newest start
#   2) otherwise the most-recently-touched mflowgen-run.log (last active step)
active_step() {
  local best="" best_t=-1 d name ts
  # (1) running steps
  for d in "$BUILD"/[0-9]*-*/; do
    [ -d "$d" ] || continue
    [ -e "${d}.time_start" ] || continue
    [ -e "${d}.time_end" ]   && continue          # finished -> not running
    ts=$(mtime "${d}.time_start")
    if [ "$ts" -gt "$best_t" ]; then best_t=$ts; best="${d%/}"; fi
  done
  if [ -n "$best" ]; then basename "$best"; return; fi
  # (2) fall back to newest run-log
  for d in "$BUILD"/[0-9]*-*/; do
    [ -d "$d" ] || continue
    [ -e "${d}${RUN_LOG}" ] || continue
    ts=$(mtime "${d}${RUN_LOG}")
    if [ "$ts" -gt "$best_t" ]; then best_t=$ts; best="${d%/}"; fi
  done
  [ -n "$best" ] && basename "$best"
}

# Point <build_dir>/current-step.log at the given step's run log (relative).
update_symlink() {
  local step="$1"
  ln -sfn "${step}/${RUN_LOG}" "$BUILD/$LINK_NAME"
}

list_steps() {
  local d name state
  printf '%-40s %s\n' "STEP" "STATE"
  for d in "$BUILD"/[0-9]*-*/; do
    [ -d "$d" ] || continue
    name=$(basename "${d%/}")
    if   [ -e "${d}.time_end" ];   then state="done"
    elif [ -e "${d}.time_start" ]; then state="RUNNING"
    else                                state="pending/copied"
    fi
    printf '%-40s %s\n' "$name" "$state"
  done
}

if [ "$mode" = "list" ]; then
  list_steps
  exit 0
fi

if [ "$mode" = "symlink" ]; then
  echo "watch_step: maintaining $BUILD/$LINK_NAME (Ctrl-C to stop)" >&2
  echo "            follow it with:  tail -F $BUILD/$LINK_NAME" >&2
  last=""
  while true; do
    step=$(active_step)
    if [ -n "$step" ] && [ "$step" != "$last" ]; then
      update_symlink "$step"; last="$step"
      echo "watch_step: -> $step" >&2
    fi
    sleep "$POLL"
  done
fi

#-- stream mode ---------------------------------------------------------------
# Stream the active step's log; when the active step changes, kill the old
# tail, print a banner, and start streaming the new one from its top.
tail_pid=""
cur=""
cleanup() { [ -n "$tail_pid" ] && kill "$tail_pid" 2>/dev/null; echo; exit 0; }
trap cleanup INT TERM

echo "watch_step: watching $BUILD (poll ${POLL}s, Ctrl-C to stop)"
echo "watch_step: symlink -> $BUILD/$LINK_NAME"

while true; do
  step=$(active_step)
  if [ -n "$step" ] && [ "$step" != "$cur" ]; then
    [ -n "$tail_pid" ] && kill "$tail_pid" 2>/dev/null
    cur="$step"
    update_symlink "$step"
    log="$BUILD/$step/$RUN_LOG"
    echo
    echo "======================================================================"
    echo "== now following: $step"
    echo "==   $log"
    echo "======================================================================"
    # Wait for the log to appear (a step can start slightly before its tee).
    for _ in $(seq 1 "$POLL" 20); do [ -e "$log" ] && break; sleep 1; done
    # -F: keep following across truncation/rotation; -n +1: show from the top.
    tail -n +1 -F "$log" &
    tail_pid=$!
  fi
  sleep "$POLL"
done
