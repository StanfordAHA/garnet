from bit_vector import BitVector
from common.model import Model


def ConfigurableModel(config_data_width, config_addr_width):
    """
    This function returns a class (parameterized by @config_data_width and
    @config_addr_width) which can be used as the base class for any functional
    model implementing a configurable module. For example if we have
    configurable module Foo:

        class Foo(ConfigurableModel(32, 32)):
            ...

    In our test code we can then do:

        foo = Foo(...)
        foo.config[addr] = data
        assert foo.config[addr] == data

    Or internally in Foo, do:

        conf = self.config[addr]

    """
    class _ConfigurableModel(Model):

        class _Map:
            def __init__(self):
                self.__map = {}

            def __getitem__(self, addr):
                if not addr.num_bits == config_addr_width:
                    raise ValueError("Expected addr to be of width "
                                     f"{config_addr_width}")
                return self.__map[addr.as_uint()]

            def __setitem__(self, addr, data):
                if not addr.num_bits == config_addr_width:
                    raise ValueError("Expected addr to be of width "
                                     f"{config_addr_width}")
                if not data.num_bits == config_data_width:
                    raise ValueError("Expected data to be of width "
                                     f"{config_data_width}")
                self.__map[addr.as_uint()] = data

        def __init__(self):
            self.__config = _ConfigurableModel._Map()

        @property
        def config(self):
            return self.__config

    return _ConfigurableModel
