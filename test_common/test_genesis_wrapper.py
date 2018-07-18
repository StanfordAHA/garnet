from collections import OrderedDict
import filecmp
import inspect
from common.genesis_wrapper import run_genesis, define_genesis_generator


TOP = "test_run_genesis"
INFILES = ["test_common/test_run_genesis.vp"]
PARAMS = {
    "width": 16,
}


def test_run_genesis():
    """
    Check operation of run_genesis() helper function against a gold output, and
    that it raises an exception on failure.
    """
    GOLDEN = "test_common/gold/test_genesis_wrapper.v"
    verilog_file = run_genesis(TOP, INFILES, PARAMS)
    res = filecmp.cmp(verilog_file, GOLDEN)
    assert res

    # Run the same command with bogus parameters injected to check that Genesis
    # fails.
    bad_params = PARAMS.copy()
    bad_params.update({"some_non_existent_param": 0})
    try:
        verilog_file = run_genesis(TOP, INFILES, bad_params)
        assert False
    except RuntimeError as e:
        msg = e.__str__()
    assert msg[:15] == "Genesis failed!"


def test_define_genesis_generator():
    def _foo(*args, **kwargs):
        pass
    fn = define_genesis_generator(TOP, INFILES, None, **PARAMS)
    assert inspect.isfunction(fn)
    assert inspect.signature(fn) == inspect.signature(_foo)
    fn()
