from common.model import Model


def test_model():
    EXPECTED_MSG = repr(TypeError("Can't instantiate abstract class Model with abstract methods __call__, __init__"))  # nopep8
    has_type_error = False
    try:
        my_model = Model()
    except TypeError as e:
        msg = e.__repr__()
        has_type_error = True
    assert has_type_error
    assert msg == EXPECTED_MSG
