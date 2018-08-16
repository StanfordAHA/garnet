from abc import abstractmethod
import generator


class Core(generator.Generator):
    @abstractmethod
    def inputs(self):
        pass

    @abstractmethod
    def outputs(self):
        pass
