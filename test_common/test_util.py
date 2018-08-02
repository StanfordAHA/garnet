import tempfile
import pathlib
from common.util import ip_available, deprecated


def test_ip_available():
    with tempfile.NamedTemporaryFile() as f:
        path = pathlib.Path(f.name)
        parent = path.parent
        assert parent.is_dir()
        assert ip_available(path.name, [str(parent)])

    assert not ip_available("random_file", ["/some/bad/path/"])


def test_deprecated():
    @deprecated("foo is deprecated")
    def foo():
        print("foo")

    try:
        foo()
        assert False
    except RuntimeError as e:
        expected_msg = "Function foo is deprecated: foo is deprecated"
        assert e.__str__() == expected_msg
