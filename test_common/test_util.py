import tempfile
import pathlib
from common.util import ip_available

def test_ip_available():
    with tempfile.TemporaryFile() as f:
        path = pathlib.Path(f)
        parent = path.parent
        assert parent.is_dir()
        assert ip_available(path.name, [str(parent)])

    assert not ip_available("random_file", ["/some/bad/path/"])
