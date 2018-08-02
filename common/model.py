from abc import ABC, abstractmethod


class Model(ABC):
    """
    This is the interface/abstract base class which should be used by all
    classes implementing a functional model. It is very bare-bones, but requires
    that subclasses implement a __call__ function, which should be the main
    mechanism of evaluating the functional model.
    """
    @abstractmethod
    def __init__(self):  # pragma: nocover
        pass

    """
    Returns the output of the functional model (in whatever form is
    appropriate). All subclasses should implement this function.
    """
    @abstractmethod
    def __call__(self, *args):  # pragma: nocover
        pass
