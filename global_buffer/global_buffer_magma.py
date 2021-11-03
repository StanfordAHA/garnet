import kratos as k
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.generator import Generator
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.global_buffer import GlobalBuffer


class GlobalBufferMagma(Generator):
    def __init__(self, _params: GlobalBufferParams):

        super().__init__()
        self._params = _params

        # instantiate global buffer kratos
        self.dut = GlobalBuffer(self._params)
        circ = k.util.to_magma(self.dut, flatten_array=True)
        self.underlying = FromMagma(circ)
    
    def name(self):
        return f"GlobalBuffer"
