from random import randint
import itertools
from collections import OrderedDict, namedtuple

__all__ = ['random', 'complete']

test_input = namedtuple('test_input', ['name', 'value'])
test_output = namedtuple('test_output', ['name', 'value'])

def random(func, n, args, outputs, with_clk=False):
    tests = []
    for i in range(n):
        _args = OrderedDict([(k, v()) for k, v in args.items()])
        if with_clk:
            for clk in [0, 1]:
                _args_copy = OrderedDict(_args)
                _args_copy["clk"] = clk
                # _args_copy["clk_en"] = randint(0, 1)
                _args_copy["clk_en"] = 1
                result = func(**_args_copy)
                test = [test_input(k, v) for k, v in _args_copy.items()] + list(outputs(result))
                tests.append(test)
        else:
            result = func(**_args)
            test = [test_input(k, v) for k, v in _args.items()] + list(outputs(result))
            tests.append(test)
    return tests

def complete(func, args, outputs):
    tests = []
    keys = [k for k in args.keys()]
    for arg_vals in itertools.product(*(value for value in args.values())):
        _args = OrderedDict([(k, v) for k, v in zip(keys, arg_vals)])
        result = func(**_args)
        test = [test_input(k, v) for k, v in _args.items()] + list(outputs(result))
        tests.append(test)
    return tests
