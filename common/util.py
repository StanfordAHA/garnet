import pytest
import shutil


def skip_unless_irun_available(fn):
    return pytest.mark.skipif(
        shutil.which("irun") is None,
        reason="irun (simulator command) not available"
    )(fn)
