from kratos import Generator
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer


def get_systemrdl_port_list(filelist):
    analyzer = VerilogDataflowAnalyzer(filelist, topmodule='glb_pio')
    analyzer.generate()
    terms = analyzer.getTerms()
    input_ports = {}
    output_ports = {}
    for tk, tv in sorted(terms.items(), key=lambda x: str(x[0])):
        name = tv.name.scopechain[-1].scopename
        if 'Output' in tv.termtype:
            output_ports[name] = int(tv.msb.value) - int(tv.lsb.value) + 1
        elif 'Input' in tv.termtype:
            input_ports[name] = int(tv.msb.value) - int(tv.lsb.value) + 1

    return input_ports, output_ports


class GlbPioWrapper(Generator):
    """GlbPioWrapper generator parses glb_pio_wrapper.sv
    generated from SystemRDL to create a Kratos wrapper"""

    def __init__(self, filename='global_buffer/systemRDL/output/glb_pio_wrapper.sv'):
        super().__init__("glb_pio")

        # get port list from the systemRDL output
        input_ports, output_ports = get_systemrdl_port_list([filename])
        for name, width in input_ports.items():
            if name == "clk":
                self.clock(name)
            elif name == "reset":
                self.reset("reset", is_async=True)
            else:
                self.input(name, width)
        for name, width in output_ports.items():
            tmp = self.output(name, width)
            self.wire(tmp, 0)
