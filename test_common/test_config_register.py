import os
import filecmp
import magma as m
from magma.bit_vector import BitVector
from magma.simulator.python_simulator import PythonSimulator
from common.config_register import define_config_register


def test_config_register():
    WIDTH = 32
    ADDR_WIDTH = 8
    ADDR_VALUE = 4

    # Check that compilation to CoreIR works. Delete JSON file afterwards.
    cr = define_config_register(WIDTH, m.bits(ADDR_VALUE, ADDR_WIDTH), True)
    m.compile("config_register", cr, output='coreir')
    gold_check = filecmp.cmp("config_register.json",
                             "test_common/gold/config_register.json")
    assert gold_check
    res = os.system("\\rm config_register.json")
    assert res == 0

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
