from common.model import Model
import sys


def test_model():
    if sys.version_info >= (3,7):
        EXPECTED_MSG = "TypeError(\"Can't instantiate abstract class Model with abstract methods __call__, __init__\")"  # nopep8
    else:
        EXPECTED_MSG = "TypeError(\"Can't instantiate abstract class Model with abstract methods __call__, __init__\",)"  # nopep8
    has_type_error = False
    try:
        my_model = Model()
    except TypeError as e:
        msg = e.__repr__()
        has_type_error = True
    assert has_type_error
    assert msg == EXPECTED_MSG
