from abc import abstractmethod
from generator.configurable import Configurable


class Core(Configurable):
    @abstractmethod
    def inputs(self):
        pass

    @abstractmethod
    def outputs(self):
        pass
