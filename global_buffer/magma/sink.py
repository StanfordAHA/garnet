import magma
from gemstone.generator.generator import Generator

class Sink(Generator):      
    def __init__(self, T):  
        super().__init__()  
        self.add_ports(     
            sink_in=T.flip()
        )                   
    def name(self):         
        return "sink" 

def connect_sink(top, port):
    sink = Sink(port.type())
    top.wire(sink.ports.sink_in, port)
    return sink
