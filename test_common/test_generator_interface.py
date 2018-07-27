import random
import string
from common.generator_interface import GeneratorInterface


def generate_random_string(k):
    return ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=k))


def generate_random(type_):
    if type_ == int:
        return random.randint(0, 100)
    if type_ == str:
        k = random.randint(0, 10)
        return generate_random_string(k)
    if type_ == float:
        return 100.0 * random.random()
    raise NotImplementedError(f"{type_}")


def test_generator_interface_basic():
    TYPES = (int, str, float,)
    N = 100
    gold = {}
    interface = GeneratorInterface()
    for _ in range(N):
        name = None
        while name is None or name in gold:
            name = generate_random_string(10)
        type_ = random.choice(TYPES)
        default = generate_random(type_)
        assert isinstance(default, type_)
        gold[name] = (type_, default,)
        interface.register(name, type_, default)

    assert interface.params == gold


def test_generator_interface_overwrite():
    interface = GeneratorInterface()
    interface.register("foo", int, 10)
    interface.register("bar", str, "hello")
    assert interface.params == {
        "foo": (int, 10,),
        "bar": (str, "hello",)
    }
    try:
        interface.register("foo", str, "foo!")
    except ValueError as e:
        assert e.__str__() == "param foo already registered"
