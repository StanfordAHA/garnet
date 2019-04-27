import fault


def gen_io_core():
    class _IOCore():
        def __init__(self):
            super().__init__()
            self.io2glb_16bit = fault.UnknownValue
            self.io2f_16bit = fault.UnknownValue
            self.io2glb_1bit = fault.UnknownValue
            self.io2f_1bit = fault.UnknownValue

        def __call__(self, glb2io_16bit, glb2io_1bit, f2io_16bit, f2io_1bit):
            self.io2f_16bit = glb2io_16bit
            self.io2f_1bit = glb2io_1bit
            self.io2glb_16bit = f2io_16bit
            self.io2glb_1bit = f2io_1bit
            return self.io2f_16bit, self.io2f_1bit,\
                self.io2glb_16bit, self.io2glb_1bit

    return _IOCore
