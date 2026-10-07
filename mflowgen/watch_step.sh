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
#   ./watch_step.sh --summary [out_dir]      # whole sweep: done / running /
#                                            #   failed / not started, and
#                                            #   whether sweep_specs.py is alive
#
#   build_dir defaults to $PWD. For the spec sweep it is the per-config dir,
#   e.g.  sweep_out/tile_memcore_pnr/fw1_dw16_sc4096_sp_in1_out1
#   --summary takes the sweep's --out-dir instead (the parent of those).
#
# A step with .time_start but no .time_end is either running or died (step
# scripts run under `set -e`, so a failed or killed step never writes
# .time_end). --list and --summary tell them apart by looking for live
# processes whose working dir is inside the step / workspace (Linux /proc).
#
# --summary, per workspace of the sweep:
#   running   a live make/mflowgen in the workspace. Shows the step, its time
#             so far, how long its log has been quiet, and the log's last line
#             (flagged when it is a Genus/Innovus/PT prompt: the tool hit an
#             error and is waiting for input -- a hang).
#   done      done.flag (sweep_specs writes it when the config's build passed).
#   failed    the workspace exists, nothing is running, no done.flag: the
#             build failed or was killed. Shows the step it stopped in.
#   not started  listed in <out_dir>/sweep_plan.txt (written by sweep_specs.py
#             at the start of each run) with no workspace yet, or a workspace
#             this run hasn't touched yet. Without the plan (sweep started
#             before sweep_specs wrote one) recreate it with the run's own
#             selection flags:  sweep_specs.py <flags> --list > <out_dir>/sweep_plan.txt
#
# No dependencies beyond bash 4 + GNU coreutils/findutils (find/stat/ln/tail).
#=============================================================================
set -u

POLL=2                       # seconds between checks
LINK_NAME="current-step.log" # symlink maintained in build_dir
RUN_LOG="mflowgen-run.log"   # per-step live log written by mflowgen

mode="stream"
case "${1:-}" in
  --symlink-only) mode="symlink"; shift ;;
  --list)         mode="list";    shift ;;
  -s|--summary)   mode="summary"; shift ;;
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

# Processes whose working dir is $1 or below, one "pid<TAB>comm<TAB>cwd" per
# line. Shells, pagers and editors are left out: a user's shell sitting in a
# workspace is not a build.
IDLE_COMMS=" bash sh dash zsh tcsh csh fish less more tail head vi vim nvim emacs nano tmux screen top htop find watch_step.sh "
procs_under() {
  local root pdir cwd comm
  root=$(readlink -f "$1")
  while IFS=$'\t' read -r pdir cwd; do
    case "$pdir" in /proc/[0-9]*) ;; *) continue ;; esac
    case "$cwd" in "$root"|"$root"/*) ;; *) continue ;; esac
    read -r comm < "$pdir/comm" 2>/dev/null || continue
    case "$IDLE_COMMS" in *" $comm "*) continue ;; esac
    printf '%s\t%s\t%s\n' "${pdir#/proc/}" "$comm" "$cwd"
  done < <(find /proc -mindepth 2 -maxdepth 2 -name cwd -printf '%h\t%l\n' 2>/dev/null)
}

# True if any procs_under line ($1) has its cwd at or below dir $2.
has_proc_in() {
  printf '%s\n' "$1" | awk -F'\t' -v s="$2" \
    '$3 == s || index($3, s "/") == 1 { f = 1 } END { exit !f }'
}

list_steps() {
  local d name state procs root
  root=$(readlink -f "$BUILD")
  procs=$(procs_under "$root")
  printf '%-40s %s\n' "STEP" "STATE"
  for d in "$BUILD"/[0-9]*-*/; do
    [ -d "$d" ] || continue
    name=$(basename "${d%/}")
    if   [ -e "${d}.time_end" ];   then state="done"
    elif [ -e "${d}.time_start" ]; then
      if has_proc_in "$procs" "$root/$name"
      then state="RUNNING"
      else state="FAILED/STOPPED (started, never finished, nothing running)"
      fi
    else                                state="pending/copied"
    fi
    printf '%-40s %s\n' "$name" "$state"
  done
}

#-- --summary -----------------------------------------------------------------
QUIET_WARN=1800   # flag a running step whose log hasn't grown for this long (s)
LIST_MAX=25       # cap on the not-started list
# The prompt a Genus / Innovus / PrimeTime / DC session sits at after its
# script stopped on an error (it waits for input instead of exiting).
PROMPT_RE='(@genus:[^>]*>|legacy_genus:[^>]*>|innovus [0-9]+>|(pt|dc|lc|icc2)_shell>) *$'

fmt_dur() {  # seconds -> 2d03h / 3h12m / 12m / 45s
  local s=$1
  if   [ "$s" -ge 86400 ]; then printf '%dd%02dh' $((s / 86400)) $((s % 86400 / 3600))
  elif [ "$s" -ge 3600 ];  then printf '%dh%02dm' $((s / 3600)) $((s % 3600 / 60))
  elif [ "$s" -ge 60 ];    then printf '%dm' $((s / 60))
  else                          printf '%ds' "$s"
  fi
}

# Newest mtime of a workspace's own bookkeeping (top-level logs, done.flag):
# when sweep_specs last started or finished a build there.
ws_touched() {
  local t
  t=$(stat -c %Y "$1"/done.flag "$1"/*.log 2>/dev/null | sort -n | tail -n 1)
  echo "${t:-0}"
}

# Step dir names of workspace $1 that started and never finished, newest first.
unfinished_steps() {
  local sd
  for sd in "$1"/[0-9]*-*/; do
    [ -e "${sd}.time_start" ] && [ ! -e "${sd}.time_end" ] || continue
    printf '%s\t%s\n' "$(mtime "${sd}.time_start")" "$(basename "${sd%/}")"
  done | sort -rn | cut -f2
}

# A python running sweep_specs.py (not an editor/pager/grep naming it).
SWEEP_RE='^[^ ]*python[0-9.]*( -[^ ]+)* [^ ]*sweep_specs\.py( |$)'

# pid of the sweep_specs.py whose --out-dir is $1 (resolved against that
# process's cwd; argparse default sweep_out/tile_memcore_pnr), if any.
find_sweep_pid() {
  local p a prev od cwd
  for p in $(pgrep -f "$SWEEP_RE"); do
    od=""; prev=""
    while IFS= read -r -d '' a; do
      case "$a" in --out-dir=*) od=${a#--out-dir=} ;; esac
      [ "$prev" = --out-dir ] && od=$a
      prev=$a
    done 2>/dev/null < "/proc/$p/cmdline"
    od=${od:-sweep_out/tile_memcore_pnr}
    cwd=$(readlink "/proc/$p/cwd" 2>/dev/null) || continue
    case "$od" in /*) ;; *) od="$cwd/$od" ;; esac
    [ "$(readlink -f "$od")" = "$1" ] && { echo "$p"; return; }
  done
}

# Descendants of pid $1 in a `ps -eo pid=,ppid=,etimes=,comm=` table ($2).
descendants() {
  awk -v root="$1" '{ pp[$1] = $2; row[$1] = $0 }
    END { d[root] = 1
          do { n = 0; for (p in pp) if (!(p in d) && (pp[p] in d)) { d[p] = 1; n++ } } while (n)
          for (p in d) if (p != root) print row[p] }' <<<"$2"
}

# pids other than $1 that hold the pipe pid $1 reads on stdin -- for a step's
# `tee`, whatever keeps its output pipe open (wherever its cwd is).
pipe_writers() {
  local link pat
  link=$(readlink "/proc/$1/fd/0" 2>/dev/null) || return 0
  case "$link" in pipe:*) ;; *) return 0 ;; esac
  pat=${link//[/\\[}; pat=${pat//]/\\]}
  find /proc/[0-9]*/fd -maxdepth 1 -lname "$pat" 2>/dev/null \
    | cut -d/ -f3 | sort -un | grep -vx "$1"
}

# "pid comm, up T, cwd D" for each pid on stdin, from table $1.
describe_pids() {
  local p row rp rpp ret rcomm
  while read -r p; do
    row=$(awk -v p="$p" '$1 == p' <<<"$1")
    [ -n "$row" ] || continue
    read -r rp rpp ret rcomm <<<"$row"
    printf '        pid %s  %s  up %s  cwd %s\n' "$rp" "$rcomm" "$(fmt_dur "$ret")" \
      "$(readlink "/proc/$rp/cwd" 2>/dev/null || echo '?')"
  done
}

# For a RUNNING workspace with no unfinished step: what its make waits on.
# Uses summary's locals (out, now, PS, makepid, held) via bash dynamic scope.
explain_make_wait() {
  local ws=$1 d="$out/$1" mk last t kids tee writers sd
  mk=${makepid[$ws]:-}
  last=$(for sd in "$d"/[0-9]*-*/; do
           [ -e "${sd}.time_end" ] && printf '%s\t%s\n' "$(mtime "${sd}.time_end")" "$(basename "${sd%/}")"
         done | sort -rn | head -n 1)
  if [ -n "$last" ]; then
    t=${last%%$'\t'*}
    echo "      no step running; last finished: ${last#*$'\t'} ($(fmt_dur $(( now - t ))) ago)"
  else
    echo "      no step started yet (mflowgen run / make setup)"
  fi
  [ -n "$mk" ] || return 0
  kids=$(descendants "$mk" "$PS")
  if [ -z "$kids" ]; then
    echo "      make (pid $mk) has no child processes: it should exit by itself"
    return 0
  fi
  echo "      make (pid $mk) is still waiting on:"
  awk '{ print $1 }' <<<"$kids" | describe_pids "$PS"
  for tee in $(awk '$4 == "tee" { print $1 }' <<<"$kids"); do
    writers=$(pipe_writers "$tee")
    [ -n "$writers" ] || continue
    held=$((held + 1))
    echo "      <<< a step's output pipe (read by tee pid $tee) is still held open by:"
    describe_pids "$PS" <<<"$writers"
    echo "      The step itself finished; make waits for that pipe to close."
    echo "      kill $(tr '\n' ' ' <<<"$writers")  -> tee ends, make goes on (the config can still PASS)"
  done
}

summary() {
  local out now plan myhost hdr pid="" host="" started="" t0=0 skip_existing=0
  local alive="unknown" how=""
  out=$(readlink -f "$BUILD"); now=$(date +%s); plan="$out/sweep_plan.txt"
  myhost=$(hostname -s 2>/dev/null || hostname)
  # A config workspace (mflowgen Makefile, NN-step dirs), not a sweep out-dir.
  if [ ! -e "$plan" ] && { [ -e "$out/Makefile" ] || compgen -G "$out/[0-9]*-*/" > /dev/null; }; then
    echo "watch_step: $out is one config's workspace; --summary takes the" \
         "sweep's --out-dir (its parent). --list shows one workspace's steps." >&2
    return 1
  fi

  # Workspaces: the plan's, in sweep order, then any others on disk.
  local -a order=() L_run=() L_fail=() L_ns=()
  local -A in_plan=() target=() seen=() live=() nprocs=() steplive=() steppids=() stepcomms=()
  local -A makepid=()
  local ws tg d s sd what
  if [ -f "$plan" ]; then
    hdr=$(head -n 1 "$plan")
    pid=$(sed -n 's/.*pid=\([0-9]*\).*/\1/p' <<<"$hdr")
    host=$(sed -n 's/.*host=\([^ ]*\).*/\1/p' <<<"$hdr")
    started=$(sed -n 's/.*started=\([^ ]*\).*/\1/p' <<<"$hdr")
    [ -n "$started" ] && t0=$(date -d "$started" +%s 2>/dev/null || echo 0)
    sed -n 2p "$plan" | grep -q -- '--skip-existing' && skip_existing=1
    while read -r ws tg; do
      case "$ws" in ''|'#'*) continue ;; esac
      [ -n "${seen[$ws]:-}" ] && continue
      seen[$ws]=1; in_plan[$ws]=1; target[$ws]=$tg; order+=("$ws")
    done < "$plan"
  fi
  for d in "$out"/*/ "$out"/standalone_synth/*/; do
    [ -d "$d" ] || continue
    ws=${d%/}; ws=${ws#"$out"/}
    [ "$ws" = standalone_synth ] && continue
    [ -n "${seen[$ws]:-}" ] && continue
    seen[$ws]=1; order+=("$ws")
  done

  # Is the sweep itself alive? pid from the plan if it ran on this host, else
  # the sweep_specs.py process whose --out-dir is this dir.
  if [ -n "$pid" ] && [ "$host" = "$myhost" ]; then
    if tr '\0' ' ' 2>/dev/null < "/proc/$pid/cmdline" | grep -q sweep_specs
    then alive="yes"; else alive="no"; fi
  elif [ -z "$pid" ]; then
    pid=$(find_sweep_pid "$out")
    if [ -n "$pid" ]; then alive="yes"; how=", found by its --out-dir"
    else alive="no"; how="none"; fi
  fi
  local PS; PS=$(ps -eo pid=,ppid=,etimes=,comm= 2>/dev/null)

  # Zip in progress: the sweep holds <zip>.partial open plus the file it is
  # compressing. Fallback: a default-named partial next to out_dir.
  local zpart="" zsrc="" fd l
  if [ "$alive" = yes ]; then
    for fd in /proc/"$pid"/fd/*; do
      case "${fd##*/}" in 0|1|2) continue ;; esac
      l=$(readlink "$fd" 2>/dev/null) || continue
      case "$l" in *.zip.partial) zpart=$l ;; "$out"/*) zsrc=$l ;; esac
    done
  fi
  [ -n "$zpart" ] || zpart=$(ls -1t "$out"_*.zip.partial 2>/dev/null | head -n 1)

  # One pass over the process table: a workspace is RUNNING while a make (or
  # the initial `mflowgen run`) has it as working dir -- sweep_specs runs
  # both there for the whole build.
  local p comm cwd rel rest
  while IFS=$'\t' read -r p comm cwd; do
    rel=${cwd#"$out"/}
    [ "$rel" = "$cwd" ] && continue
    if [[ $rel == standalone_synth/* ]]; then
      rest=${rel#standalone_synth/}; ws="standalone_synth/${rest%%/*}"
    else
      ws=${rel%%/*}
    fi
    rest=${rel#"$ws"}; rest=${rest#/}
    nprocs[$ws]=$(( ${nprocs[$ws]:-0} + 1 ))
    if [ -n "$rest" ]; then
      steplive[$ws/${rest%%/*}]=1
      steppids[$ws/${rest%%/*}]+="$p "
      stepcomms[$ws/${rest%%/*}]+="$comm "
    fi
    if [ -z "$rest" ]; then
      case "$comm" in make|mflowgen) live[$ws]=1; [ "$comm" = make ] && makepid[$ws]=$p ;; esac
    fi
  done < <(procs_under "$out")

  local n_done=0
  # ${a[@]+"${a[@]}"}: an empty array under set -u is an error before bash 4.4
  for ws in ${order[@]+"${order[@]}"}; do
    d="$out/$ws"
    if [ -n "${live[$ws]:-}" ]; then L_run+=("$ws"); continue; fi
    if [ ! -d "$d" ]; then L_ns+=("$ws"); continue; fi
    # A workspace the live run hasn't reached yet holds an older run's result.
    if [ "$alive" = yes ] && [ -n "${in_plan[$ws]:-}" ] \
       && [ "$(ws_touched "$d")" -lt "$t0" ]; then
      if [ -e "$d/done.flag" ] && [ "$skip_existing" = 1 ]
      then n_done=$((n_done + 1))
      else L_ns+=("$ws  (older workspace, queued for rebuild)")
      fi
      continue
    fi
    if [ -e "$d/done.flag" ]; then n_done=$((n_done + 1)); else L_fail+=("$ws"); fi
  done

  #-- header
  echo "== sweep: $out   ($(date '+%a %b %d %H:%M'))"
  case "$alive" in
    yes) echo "   sweep_specs.py: RUNNING (pid $pid, up $(fmt_dur "$(ps -o etimes= -p "$pid" | tr -d ' ')")$how)" ;;
    no)  if [ "$how" = none ]; then
           echo "   sweep_specs.py: none running on $myhost with this --out-dir"
           local others
           others=$(pgrep -af "$SWEEP_RE" | cut -c1-150)
           [ -n "$others" ] && { echo "      other sweeps here:"; sed 's/^/        /' <<<"$others"; }
         else
           echo "   sweep_specs.py: NOT running (pid $pid, started $started, has exited)"
         fi ;;
    *)   echo "   sweep_specs.py: ran on $host (pid $pid); can't check it from $myhost" ;;
  esac
  if [ -n "$zpart" ] && [ "$alive" = yes ]; then
    echo "   zip: $(du -h "$zpart" 2>/dev/null | cut -f1) so far in $zpart" \
         "(last write $(fmt_dur $(( now - $(mtime "$zpart") ))) ago)"
    [ -n "$zsrc" ] && echo "        compressing now: ${zsrc#"$out"/} ($(du -h "$zsrc" 2>/dev/null | cut -f1))"
  elif [ -n "$zpart" ]; then
    echo "   leftover $zpart: an interrupted zip (no sweep is writing it)"
    zpart=""
  fi
  local ns_count="${#L_ns[@]}"
  [ -f "$plan" ] || ns_count="?"
  echo "   ${#order[@]} workspaces: $n_done done, ${#L_run[@]} running," \
       "${#L_fail[@]} failed/stopped, $ns_count not started"
  [ -f "$plan" ] || echo "   (no sweep_plan.txt: configs that never started are invisible;" \
    "create it with  sweep_specs.py <the run's selection flags> --list > $plan)"

  #-- running
  local stuck=0 quiet_n=0 held=0 step log ins quiet last flag
  if [ ${#L_run[@]} -gt 0 ]; then
    echo; echo "RUNNING (${#L_run[@]})"
    for ws in "${L_run[@]}"; do
      d="$out/$ws"; step=""
      for s in $(unfinished_steps "$d"); do        # prefer one with live processes
        [ -n "${steplive[$ws/$s]:-}" ] && { step=$s; break; }
      done
      [ -n "$step" ] || step=$(unfinished_steps "$d" | head -n 1)
      printf '  %s%s\n' "$ws" "${target[$ws]:+   -> ${target[$ws]}}"
      if [ -z "$step" ]; then
        explain_make_wait "$ws"
        continue
      fi
      log="$d/$step/$RUN_LOG"
      ins=$(( now - $(mtime "$d/$step/.time_start") ))
      quiet=$(( now - $(mtime "$log") ))
      last=$(tail -n 20 "$log" 2>/dev/null | tr -d '\r' | awk 'NF { l = $0 } END { print l }' | cut -c1-110)
      flag=""
      if grep -qE "$PROMPT_RE" <<<"$last"; then
        flag="   <<< AT TOOL PROMPT: stopped on an error, waiting for input forever"
        [ -n "${steppids[$ws/$step]:-}" ] && flag="$flag
      to fail just this config:  kill ${steppids[$ws/$step]% }   (${stepcomms[$ws/$step]% })"
        stuck=$((stuck + 1))
      elif [ "$quiet" -ge "$QUIET_WARN" ]; then
        flag="   <<< no log output for $(fmt_dur "$quiet")"
        quiet_n=$((quiet_n + 1))
      fi
      printf '      %s: %s in step, log quiet %s%s\n' "$step" "$(fmt_dur "$ins")" "$(fmt_dur "$quiet")" "$flag"
      printf '      | %s\n' "$last"
    done
  fi

  #-- failed / stopped
  if [ ${#L_fail[@]} -gt 0 ]; then
    echo; echo "FAILED / STOPPED (${#L_fail[@]})  -- workspace exists, nothing running, no done.flag"
    for ws in "${L_fail[@]}"; do
      d="$out/$ws"
      step=$(unfinished_steps "$d" | head -n 1)
      if [ -n "$step" ]; then
        what="died in $step"; log="$ws/$step/$RUN_LOG"
      else
        step=$(for sd in "$d"/[0-9]*-*/; do
                 [ -e "${sd}.time_end" ] && printf '%s\t%s\n' "$(mtime "${sd}.time_end")" "$(basename "${sd%/}")"
               done | sort -rn | head -n 1 | cut -f2)
        if [ -n "$step" ]; then what="stopped after $step"; else what="no step ran"; fi
        log="$ws/make.log"; [ -e "$d/make.log" ] || log="$ws/mflowgen_run.log"
      fi
      [ -n "${nprocs[$ws]:-}" ] && what="$what; ${nprocs[$ws]} process(es) still have their cwd in it"
      printf '  %-48s %s\n      log: %s\n' "$ws" "$what" "$log"
    done
  fi

  #-- not started
  if [ ${#L_ns[@]} -gt 0 ]; then
    echo; echo "NOT STARTED (${#L_ns[@]})"
    local i=0
    for ws in "${L_ns[@]}"; do
      i=$((i + 1))
      if [ $i -gt $LIST_MAX ]; then echo "  ... and $(( ${#L_ns[@]} - LIST_MAX )) more (see $plan)"; break; fi
      printf '  %s%s\n' "$ws" "${target[${ws%% *}]:+   -> ${target[${ws%% *}]}}"
    done
  fi

  #-- verdict: is the sweep still doing something?
  echo
  if [ "$alive" = yes ]; then
    if [ ${#L_run[@]} -gt 0 ]; then
      echo "-> sweep_specs.py is waiting on ${#L_run[@]} running build(s)." \
           "It prints nothing more until each one ends (PASS/FAIL line)."
      [ $held -gt 0 ] && echo "   $held with every step finished, waiting on a process that holds the" \
           "step's output pipe (see above): kill it and that config completes."
      [ $stuck -gt 0 ] && echo "   $stuck at a tool prompt: they never finish on their own. Kill" \
           "the tool (pids above); its config FAILs and the sweep moves on."
      [ $quiet_n -gt 0 ] && echo "   $quiet_n with no log output for >$(fmt_dur $QUIET_WARN):" \
           "check the step's logs/ (the tool's own log) before calling it a hang."
    elif [ ${#L_ns[@]} -gt 0 ]; then
      echo "-> ${#L_ns[@]} config(s) still to start but none running right now" \
           "(between configs, or check the sweep's terminal)."
    elif [ -n "$zpart" ]; then
      echo "-> all builds finished; sweep_specs.py is writing the zip (see zip: above;" \
           "it prints nothing until 'Wrote'). Re-run to see it grow."
    else
      echo "-> all builds finished; sweep_specs.py is post-processing" \
           "(correlation.csv, then the zip if --zip)."
    fi
  elif [ "$alive" = no ]; then
    if [ ${#L_run[@]} -gt 0 ]; then
      echo "-> sweep_specs.py has exited but ${#L_run[@]} build(s) still run on their own."
    elif [ ${#L_ns[@]} -gt 0 ]; then
      echo "-> sweep_specs.py exited before starting ${#L_ns[@]} config(s)."
    else
      echo "-> sweep finished."
    fi
  else
    echo "-> ${#L_run[@]} build(s) running here now."
  fi
  return 0
}

if [ "$mode" = "list" ]; then
  list_steps
  exit 0
fi

if [ "$mode" = "summary" ]; then
  summary
  exit $?
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
