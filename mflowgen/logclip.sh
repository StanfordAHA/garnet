#!/usr/bin/env bash
#=============================================================================
# logclip.sh -- copy an mflowgen build log to your LOCAL clipboard over ssh+tmux
#=============================================================================
# Uses OSC 52: an escape sequence the terminal carries back through ssh and
# tmux to your local machine's clipboard -- no X11 / xclip / pbcopy needed.
#
# By default it copies the log of the step that is currently RUNNING (has a
# .time_start but no .time_end), falling back to the most-recently-touched
# step. It tails the log so it stays under the OSC 52 size limit.
#
# Usage:
#   ./logclip.sh [build_dir] [options]
#     build_dir                per-config workspace (default: $PWD)
#     --all                    concat every step's mflowgen-run.log, in order
#     --make                   the top-level make.log instead of a step log
#     --step <NN-name>         a specific step dir's mflowgen-run.log
#     --lines N                tail last N lines (default 4000; 0 = whole file)
#     --print                  also echo the content to the terminal
#
# One-time setup so tmux forwards the clipboard:
#   ~/.tmux.conf:   set -g set-clipboard on
#                   set -g allow-passthrough on
#   and enable clipboard-write / OSC52 in your LOCAL terminal (iTerm2: "Allow
#   clipboard access to terminal apps"; kitty/wezterm/alacritty: on/configurable).
#=============================================================================
set -u

RUN_LOG="mflowgen-run.log"
LINES=4000
MODE="active"     # active | all | make | step
STEP=""
DO_PRINT=0
BUILD=""

while [ $# -gt 0 ]; do
  case "$1" in
    --all)   MODE="all" ;;
    --make)  MODE="make" ;;
    --step)  MODE="step"; STEP="${2:-}"; shift ;;
    --lines) LINES="${2:-4000}"; shift ;;
    --print) DO_PRINT=1 ;;
    -h|--help) grep '^#' "$0" | sed 's/^#//'; exit 0 ;;
    *) BUILD="$1" ;;
  esac
  shift
done
BUILD="${BUILD:-$PWD}"; BUILD="${BUILD%/}"
[ -d "$BUILD" ] || { echo "logclip: no such build dir: $BUILD" >&2; exit 1; }

mtime() { stat -c %Y "$1" 2>/dev/null || echo 0; }

# basename of the step to follow: a running step (newest .time_start) else the
# most-recently-touched run log.
active_step() {
  local best="" best_t=-1 d ts
  for d in "$BUILD"/[0-9]*-*/; do
    [ -e "${d}.time_start" ] || continue
    [ -e "${d}.time_end" ]   && continue
    ts=$(mtime "${d}.time_start")
    [ "$ts" -gt "$best_t" ] && { best_t=$ts; best="${d%/}"; }
  done
  if [ -n "$best" ]; then basename "$best"; return; fi
  for d in "$BUILD"/[0-9]*-*/; do
    [ -e "${d}${RUN_LOG}" ] || continue
    ts=$(mtime "${d}${RUN_LOG}")
    [ "$ts" -gt "$best_t" ] && { best_t=$ts; best="${d%/}"; }
  done
  [ -n "$best" ] && basename "$best"
}

# Collect the requested text on stdout.
collect() {
  case "$MODE" in
    make)
      local f="$BUILD/make.log"; [ -f "$f" ] || { echo "logclip: no make.log in $BUILD" >&2; return 1; }
      echo "===== make.log ($BUILD) ====="; tail_or_all "$f" ;;
    all)
      local d
      for d in "$BUILD"/[0-9]*-*/; do
        [ -e "${d}${RUN_LOG}" ] || continue
        echo "===== $(basename "${d%/}") ====="; tail_or_all "${d}${RUN_LOG}"; echo
      done ;;
    step)
      local f="$BUILD/$STEP/$RUN_LOG"; [ -f "$f" ] || { echo "logclip: no $f" >&2; return 1; }
      echo "===== $STEP ====="; tail_or_all "$f" ;;
    active)
      local s; s=$(active_step)
      [ -n "$s" ] || { echo "logclip: no step logs found in $BUILD" >&2; return 1; }
      local f="$BUILD/$s/$RUN_LOG"; [ -f "$f" ] || { echo "logclip: no log for step $s" >&2; return 1; }
      echo "===== $s ====="; tail_or_all "$f" ;;
  esac
}
tail_or_all() { if [ "$LINES" -eq 0 ]; then cat "$1"; else tail -n "$LINES" "$1"; fi; }

# Copy stdin to the local clipboard via OSC 52 (tmux-aware).
osc52_copy() {
  local data b64 n limit=74994
  data="$(cat)"
  b64="$(printf %s "$data" | base64 | tr -d '\n')"
  n=${#b64}
  if [ "$n" -gt "$limit" ]; then
    echo "logclip: WARNING base64 is ${n}B (> ~${limit}B OSC52 limit); may be truncated." >&2
    echo "         re-run with a smaller --lines (or --make) to trim." >&2
  fi
  if [ -n "${TMUX:-}" ] && command -v tmux >/dev/null 2>&1; then
    # tmux forwards to the outer terminal's clipboard when set-clipboard is on.
    printf %s "$data" | tmux load-buffer -w - 2>/dev/null \
      && { echo "logclip: copied ${#data}B via tmux (OSC52)"; return; }
  fi
  # Raw OSC 52, wrapped for tmux/screen passthrough if needed.
  if [ -n "${TMUX:-}" ]; then
    printf '\033Ptmux;\033\033]52;c;%s\007\033\\' "$b64"
  elif [ "${TERM:-}" != "${TERM#screen}" ]; then
    printf '\033P\033]52;c;%s\007\033\\' "$b64"
  else
    printf '\033]52;c;%s\007' "$b64"
  fi
  echo "logclip: emitted OSC52 for ${#data}B (needs local-terminal clipboard write enabled)" >&2
}

content="$(collect)" || exit 1
[ "$DO_PRINT" -eq 1 ] && printf '%s\n' "$content"
printf %s "$content" | osc52_copy
