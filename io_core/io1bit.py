import fault


def gen_io1bit():
    class _IO1Bit():
        def __init__(self):
            super().__init__()
            self.io2glb = fault.UnknownValue
            self.io2f = fault.UnknownValue

        def __call__(self, glb2io, f2io):
            self.io2glb = f2io
            self.io2f = glb2io
            return self.io2glb, self.io2f

    return _IO1Bit
