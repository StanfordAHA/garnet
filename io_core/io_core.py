import fault


def gen_io_core():
    class _IOCore():
        def __init__(self):
            super().__init__()
            self.io2glb_16 = fault.UnknownValue
            self.io2f_16 = fault.UnknownValue
            self.io2glb_1 = fault.UnknownValue
            self.io2f_1 = fault.UnknownValue

        def __call__(self, glb2io_16, glb2io_1, f2io_16, f2io_1):
            self.io2f_16 = glb2io_16
            self.io2f_1 = glb2io_1
            self.io2glb_16 = f2io_16
            self.io2glb_1 = f2io_1
            return self.io2f_16, self.io2f_1,\
                self.io2glb_16, self.io2glb_1

    return _IOCore
