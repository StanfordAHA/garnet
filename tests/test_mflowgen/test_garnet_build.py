"""mflowgen/common/rtl/garnet_build.sh, the rtl step's in-container garnet
build: a run that printed "- garnet.py DONE" and wrote garnet.v counts even if
the process then died (heap corruption at exit), and each attempt has a
timeout (the same corruption once hung a rebuild for 14 hours)."""
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "mflowgen" / "common" / "rtl" / "garnet_build.sh"

# Stands in for python: `<stub> garnet.py <flags>`. STUB_MODES lists one mode
# per attempt; the attempt number is kept in a counter file.
STUB = """#!/bin/bash
n=$(( $(cat count 2>/dev/null || echo 0) + 1 )); echo $n > count
mode=$(echo $STUB_MODES | cut -d, -f$n)
echo "stub attempt $n mode $mode args $*"
case $mode in
  ok)       echo module top > garnet.v; echo "- garnet.py DONE"; exit 0 ;;
  done_die) echo module top > garnet.v; echo "- garnet.py DONE"; echo "double free or corruption (out)"; kill -ABRT $$ ;;
  die)      kill -ABRT $$ ;;
  done_nov) echo "- garnet.py DONE"; kill -ABRT $$ ;;
  hang)     sleep 30 ;;
esac
"""


def run(tmp_path, modes, timeout="5"):
    stub = tmp_path / "stub_python"
    stub.write_text(STUB)
    stub.chmod(0o755)
    env = dict(os.environ, GARNET_DIR=str(tmp_path), GARNET_PYTHON=str(stub),
               GARNET_BUILD_TIMEOUT=timeout, STUB_MODES=modes)
    r = subprocess.run(["bash", str(SCRIPT), "--width", "4"], env=env, capture_output=True, text=True,
                       timeout=120)
    attempts = int((tmp_path / "count").read_text()) if (tmp_path / "count").exists() else 0
    return r.returncode, attempts, r.stdout + r.stderr


@pytest.mark.parametrize("modes,rc,attempts,msg", [
    ("ok", 0, 1, ""),
    ("done_die", 0, 1, "accepting it"),            # finished build, crash at exit: no rebuild
    ("die,ok", 0, 2, "attempt 1 failed"),          # crash before DONE: rebuilt
    ("die,die,die", 1, 3, "failed 3 times"),
])
def test_garnet_build_attempts(tmp_path, modes, rc, attempts, msg):
    got_rc, got_attempts, out = run(tmp_path, modes)
    assert (got_rc, got_attempts) == (rc, attempts), out
    assert msg in out
    assert "args garnet.py --width 4" in out


def test_garnet_build_timeout(tmp_path):
    """A hung attempt is killed after GARNET_BUILD_TIMEOUT and the next one runs."""
    got_rc, got_attempts, out = run(tmp_path, "hang,ok", timeout="1")
    assert (got_rc, got_attempts) == (0, 2), out
    assert "attempt 1 timed out" in out


def test_garnet_build_needs_garnet_v(tmp_path):
    """DONE without a garnet.v (stale or missing output) is not accepted."""
    got_rc, got_attempts, out = run(tmp_path, "done_nov,ok")
    assert (got_rc, got_attempts) == (0, 2), out
    assert "accepting" not in out
