from abc import ABC, abstractmethod


class Generator(ABC):
    def __init__(self):
        self.__generated = False

    def generate(self):
        if self.__generated:
            raise Exception(f"Can not call generate multiple times")
        ret = self._generate_impl()
        self.__generated = True
        return ret

    @abstractmethod
    def _generate_impl(self):
        pass
