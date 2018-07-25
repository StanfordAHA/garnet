class GeneratorInterface:
    def __init__(self):
        self.__params = {}

    def register(self, name, type_, default):
        if name in self.__params:
            raise ValueError(f"param {name} already registered")
        self.__params[name] = (type_, default,)
        return self

    @property
    def params(self):
        return self.__params.copy()
