import os
import filecmp
import magma as m
from bit_vector import BitVector
from magma.simulator.coreir_simulator import CoreIRSimulator
from common.config_register import define_config_register
from common.util import check_files_equal


def test_config_register():
    WIDTH = 32
    ADDR_WIDTH = 8
    ADDR_VALUE = 4

    # Check that compilation to CoreIR works. Delete JSON file afterwards.
    cr = define_config_register(WIDTH, m.bits(ADDR_VALUE, ADDR_WIDTH), True)
    m.compile("config_register", cr, output='coreir')
    gold_check = check_files_equal("config_register.json",
                                   "test_common/gold/config_register.json")
    assert gold_check
    res = os.system("\\rm config_register.json")
    assert res == 0

    # Check the module against a simple simulation.
    simulator = CoreIRSimulator(cr, clock=cr.CLK)

    def reg_value():
        return simulator.get_value(cr.O)

    def step(I, addr):
        simulator.set_value(cr.I, I)
        simulator.set_value(cr.addr, addr)
        simulator.set_value(cr.CE, 1)
        simulator.advance(2)
        return reg_value()

    assert BitVector(reg_value()) == BitVector(0, WIDTH)
    sequence = [(0, 0, 0),
                (12, 4, 12),
                (0, 0, 12),
                (9, 4, 9)]
    for (I, addr, out_expected) in sequence:
        out = step(BitVector(I, WIDTH), BitVector(addr, ADDR_WIDTH))
        assert BitVector(out) == BitVector(out_expected, WIDTH)


def test_error():
    try:
        define_config_register(32, m.bits(4, 8), True, None)
        assert False, "Should throw a ValueError"
    except ValueError as e:
        assert str(e) == "Argument _type must be Bits, UInt, or SInt"
    try:
        define_config_register(32, None, True)
        assert False, "Should throw a ValueError"
    except ValueError as e:
        assert str(e) == ("Argument address must be instance of "
                          "Bits, UInt, or SInt")
