import subprocess
import os


GARNET_FILENAME = os.path.join(os.path.dirname(__file__),
                               os.path.pardir, os.path.pardir,
                               "garnet.py")


def test_garnet():
    garnet_root = os.path.dirname(GARNET_FILENAME)
    subprocess.check_call(["python", GARNET_FILENAME, "-v", "--use_sim_sram", "--rv", "--sparse-cgra", "--sparse-cgra-combined"], cwd=garnet_root)
    assert os.path.isfile("garnet.v")
