from kratos import Generator
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.gen_global_buffer_rdl import gen_global_buffer_rdl, run_systemrdl, gen_glb_pio_wrapper
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

    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_pio")
        self._params = _params

        # TODO: For now, we run systemRDL to generate SV and parse it.
        # However, in the future, we need to generate wrapper directly from configuration space.
        if not self.__class__.cache:
            garnet_home = pathlib.Path(__file__).parent.parent.parent.resolve()

            top_name = "glb"
            glb_rdl = gen_global_buffer_rdl(name=top_name, params=_params)

            # Dump rdl file
            rdl_file = os.path.join(garnet_home, "global_buffer/systemRDL/glb.rdl")
            glb_rdl.dump_rdl(rdl_file)

            # Run ORDT to generate RTL
            ordt_path = os.path.join(garnet_home, 'systemRDL', 'Ordt.jar')
            rdl_parms_file = os.path.join(
                garnet_home, "global_buffer/systemRDL/ordt_params/glb.parms")
            rdl_output_folder = os.path.join(
                garnet_home, "global_buffer/systemRDL/output/")
            run_systemrdl(ordt_path, top_name, rdl_file,
                        rdl_parms_file, rdl_output_folder)

            # Create wrapper of glb_pio.sv
            pio_file = rdl_output_folder + top_name + "_pio.sv"
            pio_wrapper_file = rdl_output_folder + top_name + "_pio_wrapper.sv"
            gen_glb_pio_wrapper(src_file=pio_file, dest_file=pio_wrapper_file)

            input_ports, output_ports = get_systemrdl_port_list([pio_wrapper_file])
            self.__class__.cache = (input_ports, output_ports)

        else:
            input_ports, output_ports = self.__class__.cache

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
