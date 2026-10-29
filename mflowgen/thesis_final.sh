#!/bin/bash
# The final thesis data set on the build machine, unattended (garnet mflowgen/CLAUDE.md
# "Final thesis data set"). Prerequisites: the thesis_fmax probes in $OUT (done 2026-10-27)
# and the two app-bundle tarballs from /aha copied to $BUILDS.
#
#   cd /sim/mstrange/BUILD_CGRA/garnet && git pull && bash mflowgen/thesis_final.sh
#
# It checks everything in the foreground (minutes), then detaches and runs in the background,
# so the terminal can be closed. Progress: tail -f $OUT/thesis_final.log. Done when
# $OUT/THESIS_FINAL_DONE exists; $OUT/thesis_final_summary.txt lists the zips to copy back.
# Re-running it resumes: every sweep part skips finished configs and make skips built steps.
# Bundles recorded later go in $BUILDS/app_bundles_thesis_dp_addon*.tgz (+ .md5); re-run to add them.
#
# Two tracks:
#   build (Innovus-bound): RTL + power-test generation for every part first (the docker
#     steps, a few hours), then thesis_tiles_pe -> thesis_dse -> thesis_filter_ab with
#     PNR_JOBS concurrent Innovus, then one lighter retry pass for any part that failed.
#   power (no Innovus): whole-CGRA power of both bundle sets. It runs next to the build track
#     when the machine has >= POWER_CONCURRENT_GB of RAM, else after it (POWER_MODE).
# Knobs (env): PNR_JOBS (4; 6 concurrent Innovus got OOM-killed before), SYNTH_JOBS (6),
# RTL_JOBS (8), POWER_TILE_JOBS (2), POWER_PAR_JOBS (4), POWER_REPLAY_JOBS (4),
# POWER_MODE (auto | concurrent | after), DRY=1 (every build command --dry-run, no pull).
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
POWER_MODE=${POWER_MODE:-auto}
POWER_CONCURRENT_GB=${POWER_CONCURRENT_GB:-160}
DRY=${DRY:-0}
NEED_GARNET=(0bc94ef9 9573a704)   # cgra_app_power --pe-registered-operands; --recipe thesis_filter_ab
DP_TGZ=$BUILDS/app_bundles_thesis_dp.tgz
DP_MD5=21b793754bd7b8ef34a076db012898ea
FP_TGZ=$BUILDS/app_bundles_thesis_fp_ab.tgz
FP_MD5=7a542f2f9a7493482fcfc3ec9ed02b45
B=$BUILDS/app_bundles_thesis_dp
F=$BUILDS/app_bundles_thesis_fp_ab
VARIANTS_DP="gaussian_agg=$B/gaussian_agg,unsharp_agg=$B/unsharp_agg,harris_agg=$B/harris_agg"
VARIANTS_DP+=",camera_pipeline_agg=$B/camera_pipeline_agg,matmul_pond_agg=$B/matmul_pond_agg"
VARIANTS_DP+=",resnet_agg=$B/resnet_agg"
VARIANTS_FP="conv_A0=$F/conv_A0,conv_A=$F/conv_A,conv_B=$F/conv_B"
# part, expected config count
PARTS=("thesis_tiles_pe 8" "thesis_dse 248" "thesis_filter_ab 10")
LOG=$OUT/thesis_final.log

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
clocks_from() {   # the table the tiles were built with, once the first clocked part wrote it
    if [ -f "$OUT/thesis_tiles_pe/thesis_clocks.json" ]; then echo "$OUT/thesis_tiles_pe/thesis_clocks.json"
    else echo "$OUT"; fi
}

preflight() {
    cd "$GARNET_DIR" || die "no garnet checkout at $GARNET_DIR"
    command -v mflowgen > /dev/null || die "mflowgen is not on PATH (activate the venv sweep_specs runs in)"
    if [ "$DRY" != 1 ]; then
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
    # bundles: extract each tarball once (md5-checked); an existing directory is used as is
    local tgz md5 dir
    for tgz in "$DP_TGZ $DP_MD5 $B" "$FP_TGZ $FP_MD5 $F"; do
        set -- $tgz
        tgz=$1 md5=$2 dir=$3
        if [ ! -d "$dir" ]; then
            [ -f "$tgz" ] || die "missing $tgz: copy it from /aha/sweep_out/ first"
            say "checking $(basename "$tgz")"
            [ "$(md5sum "$tgz" | cut -c1-32)" = "$md5" ] || die "md5 mismatch: $tgz (re-copy it)"
            tar xzf "$tgz" -C "$BUILDS" || die "extracting $tgz failed"
        fi
        [ -d "$dir" ] || die "$tgz did not extract to $dir"
    done
    # bundles recorded later (same tree, e.g. after a compiler fix): app_bundles_thesis_dp_addon*.tgz,
    # checked against <tgz>.md5 when present. A power run already in flight ignores them; run this
    # script again afterwards and the power run resumes, adding only the new bundles.
    local addon
    for addon in "$BUILDS"/app_bundles_thesis_dp_addon*.tgz; do
        [ -f "$addon" ] || continue
        [ -f "$addon.extracted" ] && continue
        if [ -f "$addon.md5" ]; then
            [ "$(md5sum "$addon" | cut -c1-32)" = "$(cut -c1-32 "$addon.md5")" ] || die "md5 mismatch: $addon"
        fi
        tar xzf "$addon" -C "$BUILDS" || die "extracting $addon failed"
        touch "$addon.extracted"
        say "added bundles from $(basename "$addon")"
    done
    # disks: docker steps die at `docker run` once /sim/docker is full (2026-10-18/19)
    df -h "$BUILDS" /sim/docker 2> /dev/null
    local gb
    gb=$(df -BG --output=avail /sim/docker 2> /dev/null | tail -1 | tr -dc 0-9)
    [ -n "$gb" ] && [ "$gb" -lt 20 ] && die "/sim/docker has ${gb} GB free: free it first (docker system df)"
    gb=$(df -BG --output=avail "$BUILDS" 2> /dev/null | tail -1 | tr -dc 0-9)
    [ -n "$gb" ] && [ "$gb" -lt 500 ] && say "WARNING: only ${gb} GB free under $BUILDS"
    # each part lists the configs it should (catches an old garnet or a missing probe)
    local part n want
    for p in "${PARTS[@]}"; do
        set -- $p
        part=$1 want=$2
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
    local mem_gb
    mem_gb=$(awk '/MemTotal/ {printf "%d", $2 / 1048576}' /proc/meminfo)
    if [ "$POWER_MODE" = auto ]; then
        if [ "$mem_gb" -ge "$POWER_CONCURRENT_GB" ]; then POWER_MODE=concurrent; else POWER_MODE=after; fi
    fi
    say "machine: $(nproc) cores, ${mem_gb} GB RAM -> power runs $POWER_MODE the build track"
    say "jobs: rtl $RTL_JOBS, DSE synth $SYNTH_JOBS, Innovus $PNR_JOBS, power tile/make/replay" \
        "$POWER_TILE_JOBS/$POWER_PAR_JOBS/$POWER_REPLAY_JOBS"
}

power_track() {
    local clk
    clk=$(clocks_from)
    say "power clocks from $clk"
    run cap --any-config --variants "$VARIANTS_DP" --clocks-from "$clk" --pe-registered-operands \
        --tile-jobs "$POWER_TILE_JOBS" --parallel-jobs "$POWER_PAR_JOBS" --replay-jobs "$POWER_REPLAY_JOBS" \
        --out-dir "$POWER_DP" --zip ||
        run cap --any-config --variants "$VARIANTS_DP" --clocks-from "$clk" --pe-registered-operands \
            --tile-jobs 1 --parallel-jobs "$POWER_PAR_JOBS" --replay-jobs "$POWER_REPLAY_JOBS" \
            --out-dir "$POWER_DP" --zip
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
    done
    # one lighter pass for what failed (e.g. an OOM-killed Innovus); finished configs are skipped
    for p in "${failed[@]}"; do
        run ss --recipe "$p" --out-dir "$OUT" --clocks-from "$OUT" --config-jobs 2 --pnr-jobs 2 \
            --skip-existing --zip --zip-slim
    done
}

summary() {
    {
        echo "thesis_final finished $(date '+%F %T') on $(hostname); garnet $(git -C "$GARNET_DIR" log -1 --format=%h)"
        local p
        for p in thesis_tiles_pe thesis_dse_mem thesis_filter_ab_mem; do
            [ -f "$OUT/$p/results.csv" ] || { echo "$p: no results.csv"; continue; }
            echo "$p: $(python3 -c "import csv, collections, sys
rows = list(csv.DictReader(open(sys.argv[1])))
print(len(rows), 'configs', dict(collections.Counter(r.get('status') for r in rows)))" "$OUT/$p/results.csv")"
        done
        for p in "$POWER_DP" "$POWER_FP"; do
            [ -f "$p/cgra_power.csv" ] || { echo "$(basename "$p"): no cgra_power.csv"; continue; }
            echo "$(basename "$p"): $(($(wc -l < "$p/cgra_power.csv") - 1)) config x variant rows;" \
                "tiles exact/replayed: $(python3 -c "import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
t = lambda k: sum(int(float(r.get(k) or 0)) for r in rows)
print(t('tiles_exact'), '/', t('tiles_replayed'))" "$p/cgra_power.csv")"
        done
        echo "upstream branch tips at start / end (an RTL push in between can mix tile RTL):"
        paste "$OUT/upstream_tips_start.txt" <(tips)
        echo "zips to copy back to /aha:"
        find "$OUT" "$BUILDS" -maxdepth 1 -name '*.zip' -newer "$OUT/upstream_tips_start.txt" -printf '  %p %s\n'
    } > "$OUT/thesis_final_summary.txt"
    cat "$OUT/thesis_final_summary.txt"
}

main() {
    say "thesis_final: pid $$, out $OUT, power $POWER_MODE"
    tips > "$OUT/upstream_tips_start.txt"
    cat "$OUT/upstream_tips_start.txt"
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
    local power_pid=
    if [ "$POWER_MODE" = concurrent ]; then
        power_track > "$OUT/thesis_final_power.log" 2>&1 &
        power_pid=$!
        say "power track running in the background (pid $power_pid, log $OUT/thesis_final_power.log)"
    fi
    build_track
    if [ -n "$power_pid" ]; then
        say "build track done; waiting for the power track"
        wait "$power_pid"
    else
        power_track 2>&1 | tee "$OUT/thesis_final_power.log"
    fi
    summary
    touch "$OUT/THESIS_FINAL_DONE"
    say "all done"
}

LOCK=$OUT/.thesis_final.lock
if [ "${THESIS_FINAL_BG:-0}" != 1 ]; then
    mkdir -p "$OUT"
    flock -n "$LOCK" true || die "another thesis_final.sh is running on $OUT"
    preflight
    rm -f "$OUT/THESIS_FINAL_DONE"
    THESIS_FINAL_BG=1 POWER_MODE=$POWER_MODE setsid nohup bash "$SELF" >> "$LOG" 2>&1 < /dev/null &
    say "started in the background (pid $!); log: $LOG"
    say "follow it with: tail -f $LOG    done when $OUT/THESIS_FINAL_DONE exists"
    exit 0
fi
exec 9> "$LOCK"
flock -n 9 || die "another thesis_final.sh is running on $OUT"
main
