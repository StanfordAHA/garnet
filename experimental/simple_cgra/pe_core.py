from core import Core


class PECore(Core):
    def __init__(self):
        super().__init__()

    def _generate_impl(self):
        raise NotImplementedError()

    def __repr__(self):
        return "PECore"
