import shutil


def irun_available():
    return shutil.which("irun") is not None


def iverilog_available():
    return shutil.which("iverilog") is not None


def verilog_sim_available():
    return irun_available() or iverilog_available()
