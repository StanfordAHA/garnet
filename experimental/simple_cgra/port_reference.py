from abc import ABC, abstractmethod


class PortReferenceBase(ABC):
    def __init__(self):
        self._ops = []

    @abstractmethod
    def get_port(self, inst):
        pass

    @abstractmethod
    def owner(self):
        pass

    @abstractmethod
    def clone(self):
        pass

    def __getitem__(self, index):
        def _fn(obj):
            return type(obj).__getitem__(obj, index)
        clone = self.clone()
        clone._ops.append(_fn)
        return clone

    def __getattr__(self, name):
        def _fn(obj):
            return getattr(obj, name)
        clone = self.clone()
        clone._ops.append(_fn)
        return clone


class PortReference(PortReferenceBase):
    def __init__(self, owner, name, T):
        super().__init__()
        self._owner = owner
        self._name = name
        self._T = T
        self._global = False

    def get_port(self, inst):
        port = getattr(inst, self._name)
        for op in self._ops:
            port = op(port)
        return port

    def owner(self):
        return self._owner

    def clone(self):
        clone = PortReference(self._owner, self._name, self._T)
        clone._ops = self._ops.copy()
        return clone
