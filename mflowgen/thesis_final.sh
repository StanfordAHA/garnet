#!/bin/bash
# The final thesis data set on the build machine, unattended (garnet mflowgen/CLAUDE.md
# "Final thesis data set"). Prerequisites: the thesis_fmax probes in $OUT (done 2026-10-27)
# and the app-bundle tarballs from /aha/sweep_out copied to $BUILDS (no .md5 needed: each
# tarball's gzip stream is tested, and a <tgz>.md5 beside it is checked when there is one).
#
#   cd /sim/mstrange/BUILD_CGRA/garnet && git pull && bash mflowgen/thesis_final.sh
#
# It checks everything in the foreground (minutes), then detaches and runs in the background,
# so the terminal can be closed. Progress: tail -f $OUT/thesis_final.log. Done when
# $OUT/THESIS_FINAL_DONE exists; $OUT/thesis_final_summary.txt lists the zips to copy back.
# Re-running it resumes: every sweep part skips finished configs and make skips built steps.
# Bundles recorded later go in $BUILDS/app_bundles_thesis_dp_addon*.tgz; re-run to add them.
# An add-on bundle that replaces one of the set drops the old bundle and its replays first, and
# a new variant directory in an add-on joins the power run. To add them while the build track
# is still running, run only the power track: POWER_ONLY=1 bash mflowgen/thesis_final.sh
# (no git pull; done when $OUT/THESIS_FINAL_POWER_DONE exists).
#
# Order: RTL + power-test generation for every part first (the docker steps, a few hours), then
# thesis_tiles_pe -> thesis_dse -> thesis_filter_ab with PNR_JOBS concurrent Innovus, one
# lighter retry pass for any part that failed, and only then the whole-CGRA app power of both
# bundle sets (it needs no Innovus, but it would slow the builds).
# Newest results at any time: $OUT/latest/ holds one zip per part and per power run, plus
# STATUS.txt. Every SNAPSHOT_MIN minutes, and right after each part or power run ends, each one
# with new results gets its CSVs rewritten from its workspaces and a fresh zip (renamed into
# place, so a copy never catches a half-written one). Copy $OUT/latest/*.zip back whenever.
# Knobs (env): PNR_JOBS (4; 6 concurrent Innovus got OOM-killed before), SYNTH_JOBS (6),
# RTL_JOBS (8), POWER_TILE_JOBS (2), POWER_PAR_JOBS (4), POWER_REPLAY_JOBS (4), SNAPSHOT_MIN (30),
# DRY=1 (every build command --dry-run, no pull, add-ons left unextracted, no snapshots),
# POWER_ONLY=1 (the power track alone, e.g. next to a running build track).
set -u
SELF=$(readlink -f "$0")

GARNET_DIR=${GARNET_DIR:-/sim/mstrange/BUILD_CGRA/garnet}
BUILDS=${BUILDS:-/nsim/mstrange/BUILDS}
OUT=${OUT:-$BUILDS/thesis_final}
POWER_DP=${POWER_DP:-$BUILDS/cgra_app_power_thesis_dp}
POWER_FP=${POWER_FP:-$BUILDS/cgra_app_power_thesis_fp_ab}
PNR_JOBS=${PNR_JOBS:-4}
SYNTH_JOBS=${SYNTH_JOBS:-6}
RTL_JOBS=${RTL_JOBS:-8}
POWER_TILE_JOBS=${POWER_TILE_JOBS:-2}
POWER_PAR_JOBS=${POWER_PAR_JOBS:-4}
POWER_REPLAY_JOBS=${POWER_REPLAY_JOBS:-4}
SNAPSHOT_MIN=${SNAPSHOT_MIN:-30}
DRY=${DRY:-0}
POWER_ONLY=${POWER_ONLY:-0}
NEED_GARNET=(0bc94ef9 9573a704)   # cgra_app_power --pe-registered-operands; --recipe thesis_filter_ab
DP_TGZ=$BUILDS/app_bundles_thesis_dp.tgz
FP_TGZ=$BUILDS/app_bundles_thesis_fp_ab.tgz
B=$BUILDS/app_bundles_thesis_dp
F=$BUILDS/app_bundles_thesis_fp_ab
# in this order (a config's first variant is its d_* reference); dp_variants appends the rest of $B
DP_KNOWN=(gaussian_agg unsharp_agg harris_agg camera_pipeline_agg matmul_pond_agg resnet_agg)
VARIANTS_FP="conv_A0=$F/conv_A0,conv_A=$F/conv_A,conv_B=$F/conv_B"
# recipe, its out dir under $OUT, expected config count
PARTS=("thesis_tiles_pe thesis_tiles_pe 8" "thesis_dse thesis_dse_mem 246" "thesis_filter_ab thesis_filter_ab_mem 10")
LATEST=$OUT/latest
LOG=$OUT/thesis_final.log
[ "$POWER_ONLY" = 1 ] && LOG=$OUT/thesis_final_power_only.log

say() { echo "[$(date '+%F %T')] $*"; }
die() { echo "*** ERROR: $*" >&2; exit 1; }
run() {
    say "START $*"
    "$@"
    local rc=$?
    say "END rc=$rc $*"
    return $rc
}
dry() { [ "$DRY" = 1 ] && echo --dry-run; }
ss() { (cd "$GARNET_DIR" && ./mflowgen/sweep_specs.py "$@" $(dry)); }
cap() { (cd "$GARNET_DIR" && ./mflowgen/cgra_app_power.py "$@" $(dry)); }
tips() {
    local r b
    for r in lake:THESIS canal:thesis gemstone:thesis lassen:thesis; do
        b=$(git ls-remote "https://github.com/StanfordAHA/${r%%:*}.git" "refs/heads/${r#*:}" 2>/dev/null | cut -c1-8)
        echo "${r%%:*} ${b:-unknown}"
    done
}
dp_variants() {   # DP_KNOWN, then every other variant directory of $B (an add-on's, e.g. resnet_pond_agg)
    local v d out=()
    for v in "${DP_KNOWN[@]}"; do out+=("$v=$B/$v"); done
    for d in "$B"/*/; do
        v=$(basename "$d")
        [[ " ${DP_KNOWN[*]} " == *" $v "* ]] && continue
        [[ "$v" =~ ^[A-Za-z0-9_]+$ ]] && compgen -G "$d*/manifest.json" > /dev/null && out+=("$v=$B/$v")
    done
    (IFS=,; echo "${out[*]}")
}
clocks_from() {   # the table the tiles were built with, once the first clocked part wrote it
    if [ -f "$OUT/thesis_tiles_pe/thesis_clocks.json" ]; then echo "$OUT/thesis_tiles_pe/thesis_clocks.json"
    else echo "$OUT"; fi
}
tgz_ok() {   # the tarball's gzip stream is whole, and it matches a <tgz>.md5 beside it if there is one
    gzip -t "$1" 2> /dev/null || return 1
    [ ! -f "$1.md5" ] || [ "$(md5sum "$1" | cut -c1-32)" = "$(cut -c1-32 "$1.md5")" ]
}

preflight() {
    cd "$GARNET_DIR" || die "no garnet checkout at $GARNET_DIR"
    command -v mflowgen > /dev/null || die "mflowgen is not on PATH (activate the venv sweep_specs runs in)"
    # (POWER_ONLY: the build track may be running from this checkout, so leave it as it is)
    if [ "$DRY" != 1 ] && [ "$POWER_ONLY" != 1 ]; then
        git pull -q --ff-only || die "git pull failed in $GARNET_DIR"
        git -C ../lake pull -q --ff-only || die "git pull failed in $GARNET_DIR/../lake"
    fi
    local c
    for c in "${NEED_GARNET[@]}"; do
        git merge-base --is-ancestor "$c" HEAD || die "garnet HEAD lacks $c: git pull"
    done
    say "garnet $(git log -1 --format='%h %s' | cut -c1-90)"
    local p
    for p in thesis_fmax_mem thesis_fmax_pe thesis_fmax_pe_regops; do
        [ -f "$OUT/$p/correlation.csv" ] || die "no $OUT/$p/correlation.csv: run --recipe thesis_fmax --out-dir $OUT first"
    done
    # bundles: extract each tarball once; an existing directory is used as is
    local tgz dir
    for tgz in "$DP_TGZ $B" "$FP_TGZ $F"; do
        set -- $tgz
        tgz=$1 dir=$2
        if [ ! -d "$dir" ]; then
            [ -f "$tgz" ] || die "missing $tgz: copy it from /aha/sweep_out/ first"
            say "checking $(basename "$tgz")"
            tgz_ok "$tgz" || die "$tgz is truncated or corrupt (re-copy it)"
            tar xzf "$tgz" -C "$BUILDS" || die "extracting $tgz failed"
        fi
        [ -d "$dir" ] || die "$tgz did not extract to $dir"
    done
    # bundles recorded later (same tree, e.g. after a compiler fix): app_bundles_thesis_dp_addon*.tgz.
    # A power run already in flight ignores them; run this script again afterwards (or
    # POWER_ONLY=1) and the power run resumes, adding only the new bundles.
    local addon vc v c ws
    for addon in "$BUILDS"/app_bundles_thesis_dp_addon*.tgz; do
        [ -f "$addon" ] || continue
        [ -f "$addon.extracted" ] && continue
        if [ "$DRY" = 1 ]; then
            say "DRY: not extracting $(basename "$addon")"
            continue
        fi
        tgz_ok "$addon" || die "$addon is truncated or corrupt (re-copy it)"
        # a bundle it replaces: drop the old one (tar would keep its stray files) and that
        # variant's replay chain in the power workspaces (make would call it up to date; the
        # next mflowgen run gives the steps new build dirs)
        while read -r vc; do
            v=${vc%%/*} c=${vc#*/}
            [ -n "$v" ] && [ -n "$c" ] && [ -d "$B/$v/$c" ] || continue
            for ws in "$POWER_DP/$c"/Tile_*; do
                [ -d "$ws" ] || continue
                rm -rf "$ws"/[0-9]*-application-"$v" "$ws"/[0-9]*-testbench-"$v" \
                    "$ws"/[0-9]*-post-synth-power-"$v"
            done
            rm -rf "${B:?}/$v/$c"
            say "replacing bundle $v/$c (and its replays, if any)"
        done < <(tar tzf "$addon" | awk -F/ -v top="$(basename "$B")" \
            '$1 == top && NF >= 3 && $3 != "" {print $2 "/" $3}' | sort -u)
        tar xzf "$addon" -C "$BUILDS" || die "extracting $addon failed"
        touch "$addon.extracted"
        say "added bundles from $(basename "$addon")"
    done
    VARIANTS_DP=$(dp_variants)
    say "DP variants: $(echo "$VARIANTS_DP" | sed "s|=[^,]*||g")"
    # disks: docker steps die at `docker run` once /sim/docker is full (2026-10-18/19)
    df -h "$BUILDS" /sim/docker 2> /dev/null
    local gb
    gb=$(df -BG --output=avail /sim/docker 2> /dev/null | tail -1 | tr -dc 0-9)
    [ -n "$gb" ] && [ "$gb" -lt 20 ] && die "/sim/docker has ${gb} GB free: free it first (docker system df)"
    gb=$(df -BG --output=avail "$BUILDS" 2> /dev/null | tail -1 | tr -dc 0-9)
    [ -n "$gb" ] && [ "$gb" -lt 500 ] && say "WARNING: only ${gb} GB free under $BUILDS"
    # each part lists the configs it should (catches an old garnet or a missing probe)
    local part n want
    [ "$POWER_ONLY" = 1 ] || for p in "${PARTS[@]}"; do
        set -- $p
        part=$1 want=$3
        n=$(cd "$GARNET_DIR" && ./mflowgen/sweep_specs.py --recipe "$part" --out-dir "$OUT" \
            --clocks-from "$OUT" --list 2> /dev/null | grep -c '^fw')
        [ "$n" = "$want" ] || die "--recipe $part lists $n configs, expected $want"
    done
    say "clock table (from the probes in $OUT):"
    (cd "$GARNET_DIR" && ./mflowgen/sweep_specs.py --recipe thesis_tiles_pe --out-dir "$OUT" \
        --clocks-from "$OUT" --list 2> /dev/null | grep 'MHz')
    # the power runs parse every bundle
    (cd "$GARNET_DIR" && ./mflowgen/cgra_app_power.py --any-config --variants "$VARIANTS_DP" \
        --clocks-from "$OUT" --pe-registered-operands --out-dir "$POWER_DP" --dry-run > /dev/null) \
        || die "cgra_app_power --dry-run fails on $B"
    (cd "$GARNET_DIR" && ./mflowgen/cgra_app_power.py --any-config --variants "$VARIANTS_FP" \
        --clocks-from "$OUT" --out-dir "$POWER_FP" --dry-run > /dev/null) \
        || die "cgra_app_power --dry-run fails on $F"
    say "machine: $(nproc) cores, $(awk '/MemTotal/ {printf "%d", $2 / 1048576}' /proc/meminfo) GB RAM"
    say "jobs: rtl $RTL_JOBS, DSE synth $SYNTH_JOBS, Innovus $PNR_JOBS, power tile/make/replay" \
        "$POWER_TILE_JOBS/$POWER_PAR_JOBS/$POWER_REPLAY_JOBS; snapshots every $SNAPSHOT_MIN min to $LATEST"
}

# ---- newest results in $LATEST while the run goes on
changed() {   # changed <stamp> <dir> <maxdepth> <file name>...: one of them under <dir> is newer
    local stamp=$1 dir=$2 depth=$3 expr=() n
    shift 3
    [ -f "$stamp" ] || return 0
    for n in "$@"; do expr+=(-o -name "$n"); done
    [ -n "$(find "$dir" -maxdepth "$depth" \( "${expr[@]:1}" \) -newer "$stamp" -print -quit 2> /dev/null)" ]
}
snapshot() {   # snapshot sweep|power <dir>: its CSVs from its workspaces + a fresh zip, if it changed
    local kind=$1 dir=$2 name zip
    name=$(basename "$dir")
    local stamp=$LATEST/.$name.stamp
    [ -d "$dir" ] || return 0
    if [ "$kind" = sweep ]; then
        changed "$stamp" "$dir" 3 .time_end done.flag results.csv || return 0
        zip=$LATEST/${name}_latest_slim.zip
    else
        changed "$stamp" "$dir" 6 .time_end '*.hier' || return 0
        zip=$LATEST/${name}_latest.zip
    fi
    touch "$stamp.new"   # before the zip, so results landing during it make the next round zip again
    if [ "$kind" = sweep ]; then
        nice -n 19 ./mflowgen/sweep_specs.py --zip-only --zip-slim --out-dir "$dir" --zip-path "$zip"
    else
        nice -n 19 ./mflowgen/cgra_app_power.py --report-only --zip --out-dir "$dir" --zip-path "$zip"
    fi > "$LATEST/.$name.log" 2>&1
    if [ $? = 0 ]; then
        mv "$stamp.new" "$stamp"
        say "snapshot: $zip"
    else
        rm -f "$stamp.new"
        say "WARNING: snapshot of $name failed (log $LATEST/.$name.log); the next round retries"
    fi
}
results_lines() {   # one line per part and power run: what is done so far
    local p
    for p in "${PARTS[@]}"; do
        set -- $p
        [ -f "$OUT/$2/results.csv" ] || { echo "$2: no results yet (of $3 configs)"; continue; }
        echo "$2: $(python3 -c "import csv, collections, sys
rows = list(csv.DictReader(open(sys.argv[1])))
print(len(rows), 'of', sys.argv[2], 'configs', dict(collections.Counter(r.get('status') for r in rows)))" \
            "$OUT/$2/results.csv" "$3")"
    done
    for p in "$POWER_DP" "$POWER_FP"; do
        [ -f "$p/cgra_power.csv" ] || { echo "$(basename "$p"): no cgra_power.csv yet"; continue; }
        echo "$(basename "$p"): $(($(wc -l < "$p/cgra_power.csv") - 1)) config x variant rows;" \
            "tiles exact/replayed: $(python3 -c "import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
t = lambda k: sum(int(float(r.get(k) or 0)) for r in rows)
print(t('tiles_exact'), '/', t('tiles_replayed'))" "$p/cgra_power.csv")"
    done
}
publish() {   # one snapshot round; one round at a time across a main and a POWER_ONLY run
    [ "$DRY" = 1 ] && return 0
    mkdir -p "$LATEST"
    (
        flock 7
        cd "$GARNET_DIR" || exit 1
        local p
        for p in "${PARTS[@]}"; do
            set -- $p
            snapshot sweep "$OUT/$2"
        done
        snapshot power "$POWER_DP"
        snapshot power "$POWER_FP"
        {
            echo "thesis_final $(date '+%F %T') on $(hostname); garnet $(git -C "$GARNET_DIR" log -1 --format=%h)"
            echo "last step: $(grep -a -E '(START|END rc=)' "$LOG" 2> /dev/null | tail -1 | cut -c1-200)"
            results_lines
            echo "zips (newest results of each; copy them back whenever):"
            find "$LATEST" -maxdepth 1 -name '*.zip' -printf '  %TY-%Tm-%Td %TH:%TM  %s  %f\n' | sort -k4
        } > "$LATEST/STATUS.txt.tmp" && mv "$LATEST/STATUS.txt.tmp" "$LATEST/STATUS.txt"
    ) 7> "$LATEST/.publish.lock"
}
publisher() {   # a round every SNAPSHOT_MIN minutes until stop_publisher
    local t
    while :; do
        publish
        for ((t = 0; t < SNAPSHOT_MIN * 60; t += 15)); do
            [ -f "$LATEST/.stop.$$" ] && return 0
            sleep 15
        done
    done
}
start_publisher() {
    PUB_PID=
    [ "$DRY" = 1 ] && return 0
    mkdir -p "$LATEST"
    rm -f "$LATEST/.stop.$$"
    publisher >> "$OUT/thesis_final_publish.log" 2>&1 &
    PUB_PID=$!
    say "newest results go to $LATEST every $SNAPSHOT_MIN min (STATUS.txt; publisher pid $PUB_PID)"
}
stop_publisher() {   # lets a round in progress finish, then publishes the final state
    [ -n "${PUB_PID:-}" ] || return 0
    touch "$LATEST/.stop.$$"
    wait "$PUB_PID"
    rm -f "$LATEST/.stop.$$"
    publish >> "$OUT/thesis_final_publish.log" 2>&1
}

power_track() {   # always in a subshell (&, a pipeline or ( )), which holds the power lock
    exec 8> "$POWER_LOCK"
    flock -n 8 || { say "WARNING: another power track holds $POWER_LOCK; not starting this one"; return 1; }
    local clk
    clk=$(clocks_from)
    say "power clocks from $clk"
    run cap --any-config --variants "$VARIANTS_DP" --clocks-from "$clk" --pe-registered-operands \
        --tile-jobs "$POWER_TILE_JOBS" --parallel-jobs "$POWER_PAR_JOBS" --replay-jobs "$POWER_REPLAY_JOBS" \
        --out-dir "$POWER_DP" --zip ||
        run cap --any-config --variants "$VARIANTS_DP" --clocks-from "$clk" --pe-registered-operands \
            --tile-jobs 1 --parallel-jobs "$POWER_PAR_JOBS" --replay-jobs "$POWER_REPLAY_JOBS" \
            --out-dir "$POWER_DP" --zip
    publish >> "$OUT/thesis_final_publish.log" 2>&1
    run cap --any-config --variants "$VARIANTS_FP" --clocks-from "$clk" \
        --tile-jobs "$POWER_TILE_JOBS" --parallel-jobs "$POWER_PAR_JOBS" --replay-jobs "$POWER_REPLAY_JOBS" \
        --out-dir "$POWER_FP" --zip ||
        run cap --any-config --variants "$VARIANTS_FP" --clocks-from "$clk" \
            --tile-jobs 1 --parallel-jobs "$POWER_PAR_JOBS" --replay-jobs "$POWER_REPLAY_JOBS" \
            --out-dir "$POWER_FP" --zip
}

build_track() {
    local p failed=()
    for p in thesis_tiles_pe thesis_dse thesis_filter_ab; do
        local jobs=(--config-jobs "$PNR_JOBS")   # no --pnr-set: config-jobs = concurrent PnRs
        [ "$p" = thesis_dse ] && jobs=(--config-jobs "$SYNTH_JOBS" --pnr-jobs "$PNR_JOBS")
        run ss --recipe "$p" --out-dir "$OUT" --clocks-from "$OUT" "${jobs[@]}" \
            --skip-existing --zip --zip-slim || failed+=("$p")
        publish >> "$OUT/thesis_final_publish.log" 2>&1
    done
    # one lighter pass for what failed (e.g. an OOM-killed Innovus); finished configs are skipped
    for p in "${failed[@]}"; do
        run ss --recipe "$p" --out-dir "$OUT" --clocks-from "$OUT" --config-jobs 2 --pnr-jobs 2 \
            --skip-existing --zip --zip-slim
        publish >> "$OUT/thesis_final_publish.log" 2>&1
    done
}

summary() {
    {
        echo "thesis_final finished $(date '+%F %T') on $(hostname); garnet $(git -C "$GARNET_DIR" log -1 --format=%h)"
        results_lines
        echo "upstream branch tips at start / end (an RTL push in between can mix tile RTL):"
        local start=$OUT/upstream_tips_start.txt
        [ -f "$start" ] || tips > "$start"
        paste "$start" <(tips)
        echo "newest results (one zip per part and power run): $LATEST"
        echo "zips to copy back to /aha (made since $(date -r "$start" '+%F %T')):"
        find "$OUT" "$BUILDS" "$LATEST" -maxdepth 1 -name '*.zip' -newer "$start" -printf '  %p %s\n'
    } > "$OUT/thesis_final_summary.txt"
    cat "$OUT/thesis_final_summary.txt"
}

main() {
    say "thesis_final: pid $$, out $OUT"
    VARIANTS_DP=$(dp_variants)
    tips > "$OUT/upstream_tips_start.txt"
    cat "$OUT/upstream_tips_start.txt"
    start_publisher
    # docker steps (rtl, memtile-power-test-gen) for every part first, so a filling /sim/docker
    # can't fail the builds days in; a part that still fails here retries them in its build
    local p
    for p in thesis_tiles_pe thesis_filter_ab thesis_dse; do
        # (--pnr-jobs sizes the DSE's PnR-set pool, default 1; the other parts ignore it)
        run ss --recipe "$p" --out-dir "$OUT" --clocks-from "$OUT" --rtl-only --skip-existing \
            --config-jobs "$RTL_JOBS" --pnr-jobs 4 ||
            run ss --recipe "$p" --out-dir "$OUT" --clocks-from "$OUT" --rtl-only --skip-existing \
                --config-jobs "$RTL_JOBS" --pnr-jobs 4 ||
            say "WARNING: $p --rtl-only still failing; its build pass retries the docker steps"
    done
    build_track
    say "build track done; whole-CGRA app power next"
    power_track 2>&1 | tee -a "$OUT/thesis_final_power.log"
    stop_publisher
    summary
    touch "$OUT/THESIS_FINAL_DONE"
    say "all done"
}

power_main() {   # POWER_ONLY=1
    say "thesis_final POWER_ONLY: pid $$, power $POWER_DP $POWER_FP"
    VARIANTS_DP=$(dp_variants)
    start_publisher
    power_track 2>&1 | tee -a "$OUT/thesis_final_power.log"
    stop_publisher
    summary
    touch "$OUT/THESIS_FINAL_POWER_DONE"
    say "power done"
}

LOCK=$OUT/.thesis_final.lock
POWER_LOCK=$OUT/.thesis_final_power.lock
DONE=$OUT/THESIS_FINAL_DONE
[ "$POWER_ONLY" = 1 ] && DONE=$OUT/THESIS_FINAL_POWER_DONE
if [ "${THESIS_FINAL_BG:-0}" != 1 ]; then
    mkdir -p "$OUT"
    # preflight swaps bundles under replays, so no power track may be running; POWER_ONLY may
    # run next to the build track
    flock -n "$POWER_LOCK" true || die "a power track is running on $POWER_DP (tail $OUT/thesis_final_power.log)"
    if [ "$POWER_ONLY" != 1 ]; then
        flock -n "$LOCK" true || die "another thesis_final.sh is running on $OUT"
    fi
    preflight
    rm -f "$DONE"
    THESIS_FINAL_BG=1 setsid nohup bash "$SELF" >> "$LOG" 2>&1 < /dev/null &
    say "started in the background (pid $!); log: $LOG"
    say "follow it with: tail -f $LOG    done when $DONE exists"
    say "newest results at any time: $LATEST (STATUS.txt + one zip per part and power run)"
    exit 0
fi
if [ "$POWER_ONLY" = 1 ]; then
    power_main
    exit
fi
exec 9> "$LOCK"
flock -n 9 || die "another thesis_final.sh is running on $OUT"
main
exit
