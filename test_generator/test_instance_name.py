import magma as m
import tempfile
from common.dummy_core_magma import DummyCore
from common.util import check_files_equal


def test_instance_name_tile():
    core = DummyCore()
    circuit = core.circuit()
    assert str(circuit.instances) == '[MuxWithDefaultWrapper_2_32_8_0_inst0 = MuxWithDefaultWrapper_2_32_8_0(), dummy_1 = ConfigRegister_32_8_32_0(name="dummy_1"), dummy_2 = ConfigRegister_32_8_32_1(name="dummy_2")]'  # noqa
    with tempfile.TemporaryDirectory() as tempdir:
        m.compile(f"{tempdir}/core", circuit)
        check_files_equal(f"{tempdir}/core.v",
                          "test_generator/gold/core_instance_name.v")
