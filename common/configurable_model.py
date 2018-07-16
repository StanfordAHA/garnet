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
        foo.configure(addr, data)
        assert foo.read_config(addr) == data

    Or internally in Foo, do:

        conf = self.__config[addr]

    """
    class _ConfigurableModel(Model):
        def __init__(self):
            self.__config = {}

        def configure(self, addr: BitVector, data: BitVector):
            assert data.num_bits == config_data_width
            assert addr.num_bits == config_addr_width
            self.__config[addr.unsigned_value] = data

        def read_config(self, addr):
            return self.__config[addr.unsigned_value]

    return _ConfigurableModel
