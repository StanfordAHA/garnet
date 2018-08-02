import shutil
import pathlib


def irun_available():
    return shutil.which("irun") is not None


def iverilog_available():
    return shutil.which("iverilog") is not None


def verilog_sim_available():
    return irun_available() or iverilog_available()


def ip_available(filename, paths):
    for path in paths:
        fullpath = pathlib.Path(path) / pathlib.Path(filename)
        if fullpath.is_file():
            return True
    return False
