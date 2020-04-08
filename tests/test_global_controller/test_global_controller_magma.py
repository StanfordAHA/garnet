import magma
from global_controller.global_controller_magma import GlobalController


def test_compile():
    global_controller = GlobalController()
    global_controller_circ = global_controller.circuit()
    magma.compile("global_controller",
                  global_controller_circ, output="coreir-verilog")
