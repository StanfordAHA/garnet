#!/bin/bash
# garnet_build.sh <garnet.py flags>: build the CGRA verilog for the rtl step,
# like `aha garnet <flags>` (python garnet.py, up to three attempts), but
#  - an attempt that printed "- garnet.py DONE" and wrote garnet.v counts as
#    done even when the process then dies: garnet.py prints DONE after
#    build_verilog, and the native kratos/coreir heap corruption that makes
#    garnet.py flaky shows up as SIGABRT "double free or corruption" at
#    interpreter exit (aha garnet retried such a finished build);
#  - every attempt is bounded by a timeout: the same corruption once hung a
#    rebuild for 14 hours (a 4x2 build takes about 2 minutes).
# Env: GARNET_DIR (default /aha/garnet), GARNET_PYTHON (default /aha/bin/python),
# GARNET_BUILD_TIMEOUT seconds per attempt (default 7200).
GARNET_DIR=${GARNET_DIR:-/aha/garnet}
PY=${GARNET_PYTHON:-/aha/bin/python}
[ -x "$PY" ] || PY=python3
TIMEOUT=${GARNET_BUILD_TIMEOUT:-7200}
cd "$GARNET_DIR" || exit 1
for attempt in 1 2 3; do
    log=$(mktemp /tmp/garnet_build.XXXXXX)
    rm -f garnet.v
    echo "--- garnet_build attempt $attempt (timeout ${TIMEOUT}s): $PY garnet.py $*"
    timeout --kill-after=60 "$TIMEOUT" "$PY" garnet.py "$@" 2>&1 | tee "$log"
    rc=${PIPESTATUS[0]}
    if [ "$rc" = 0 ]; then
        exit 0
    fi
    if grep -q -- "- garnet.py DONE" "$log" && [ -s garnet.v ]; then
        echo "--- garnet_build: garnet.py finished (DONE, garnet.v written) but exited rc=$rc; accepting it"
        exit 0
    fi
    if [ "$rc" = 124 ] || [ "$rc" = 137 ]; then
        echo "*** garnet_build attempt $attempt timed out after ${TIMEOUT}s"
    else
        echo "*** garnet_build attempt $attempt failed (rc=$rc)"
    fi
done
echo "*** ERROR: garnet_build: garnet.py failed 3 times"
exit 1
