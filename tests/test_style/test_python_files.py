"""Checks over every git-tracked .py file in garnet:

- each one compiles (most scripts and mflowgen constructs have no other test);
- pycodestyle passes with setup.cfg's [pycodestyle] section, the config garnet's
  lint uses. Skipped when pycodestyle is not installed (`pip install pycodestyle`).
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def tracked_py_files():
    # safe.directory: CI copies the checkout into a container as another user
    cmd = ["git", "-c", "safe.directory=*", "-C", str(ROOT), "ls-files", "*.py"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    except OSError as e:
        pytest.skip(f"git not available: {e}")
    except subprocess.CalledProcessError as e:
        pytest.skip(f"not a git checkout: {e.stderr.strip()}")
    return out.split()


def test_tracked_python_files_compile():
    bad = []
    for f in tracked_py_files():
        try:
            compile((ROOT / f).read_bytes(), f, "exec")
        except SyntaxError as e:
            bad.append(f"{f}:{e.lineno}: {e.msg}")
    assert not bad, "files that do not compile:\n" + "\n".join(bad)


def test_pycodestyle():
    pytest.importorskip("pycodestyle")
    # Run from the repo root so pycodestyle reads setup.cfg as the project config
    res = subprocess.run([sys.executable, "-m", "pycodestyle"] + tracked_py_files(),
                         cwd=ROOT, capture_output=True, text=True)
    assert res.returncode == 0, f"pycodestyle (setup.cfg) failed:\n{res.stdout[-20000:]}{res.stderr}"
