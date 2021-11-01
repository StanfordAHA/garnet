from kratos import Generator
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer
import pathlib
import os


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
    cache = None

    def __init__(self):
        super().__init__("glb_pio")

        garnet_home = pathlib.Path(__file__).parent.parent.parent.resolve()
        filename = os.path.join(
            garnet_home, 'global_buffer/systemRDL/output/glb_pio_wrapper.sv')
        # get port list from the systemRDL output
        if self.__class__.cache:
            input_ports, output_ports = self.__class__.cache
        else:
            input_ports, output_ports = get_systemrdl_port_list([filename])
            self.__class__.cache = (input_ports, output_ports)
        for name, width in input_ports.items():
            if name == "clk":
                self.clock(name)
            elif name == "reset":
                self.reset("reset", is_async=True)
            else:
                self.input(name, width)
        for name, width in output_ports.items():
            self.output(name, width)

        self.external = True
