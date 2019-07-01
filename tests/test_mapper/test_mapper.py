import subprocess
import os


GARNET_FILENAME = os.path.join(os.path.dirname(__file__),
                               os.path.pardir, os.path.pardir,
                               "garnet.py")

curidir = "tests/test_mapper"
infile = "tests/test_mapper/pointwise.json"
outfile = "tests/test_mapper/_pointwise.bs"


def test_pointwise():
    garnet_root = os.path.dirname(GARNET_FILENAME)
    subprocess.check_call([
        "python", GARNET_FILENAME, "--no-pd",
        "--input-app", infile,
        "--width", "8",
        "--height", "2",
        "--output-file", outfile
    ], cwd=garnet_root)
    assert os.path.isfile(outfile)
