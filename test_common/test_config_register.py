import os
import magma as m
from magma.bit_vector import BitVector
from magma.simulator.python_simulator import PythonSimulator
from common.config_register import DefineConfigRegister
from common.util import make_relative


def test_config_register():
    WIDTH = 32
    ADDR_WIDTH = 8
    ADDR_VALUE = 4

    # Check that compilation to CoreIR works. Delete JSON file afterwards.
    cr = DefineConfigRegister(WIDTH, m.bits(ADDR_VALUE, ADDR_WIDTH), True)
    m.compile("config_register", cr, output='coreir')
    os.system(f"\\rm {make_relative('config_register.json')}")

    # Check the module against a simple simulation.
    simulator = PythonSimulator(cr, clock=cr.CLK)

    def reg_value():
        return simulator.get_value(cr.O)

    def step(I, addr):
        simulator.set_value(cr.I, I)
        simulator.set_value(cr.addr, addr)
        simulator.advance(2)
        return reg_value()

    assert reg_value() == BitVector(0, WIDTH)
    sequence = [(0, 0, 0),
                (12, 4, 0),
                (0, 0, 12),
                (0, 0, 12)]
    for (I, addr, out_expected) in sequence:
        out = step(BitVector(I, WIDTH), BitVector(addr, ADDR_WIDTH))
        assert out == BitVector(out_expected, WIDTH)
