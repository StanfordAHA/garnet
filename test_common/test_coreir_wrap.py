import pytest
import tempfile
import magma
from common.coreir_wrap import CoreirWrap


# TODO(rsetaluri): Add 'Clock' to types, once
# https://github.com/phanrahan/magma/pull/289 is merged.
types = [magma.AsyncReset]


@pytest.mark.parametrize("T", types)
def test_coreir_wrap(T):
    wrapper = CoreirWrap(T, magma.Bit, "Bit")

    assert wrapper.out_type == T
    assert wrapper.in_type == magma.Bit
    assert wrapper.type_name == "Bit"

    wrapper_circuit = wrapper.circuit()

    test_circuit = magma.DefineCircuit(
        "TestCircuit", "O", magma.Out(T))
    wrapper_inst = wrapper_circuit()
    magma.wire(magma.bit(0), wrapper_inst.I)
    magma.wire(wrapper_inst.O, test_circuit.O)
    magma.EndCircuit()

    magma.compile("TEST", test_circuit, output="coreir")
