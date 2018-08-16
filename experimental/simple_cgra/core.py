from abc import abstractmethod
from configurable import Configurable


class Core(Configurable):
    @abstractmethod
    def inputs(self):
        pass

    @abstractmethod
    def outputs(self):
        pass
