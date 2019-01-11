from typing import Dict, List
import argparse
import magma as m
from common.run_genesis import run_genesis


default_type_map = {"clk": m.In(m.Clock),
                    "reset": m.In(m.AsyncReset),
                    "config_en": m.In(m.Enable)}


class GenesisWrapper:
    def __init__(self, interface, top_name, default_infiles,
                 system_verilog=False, type_map={}):
        """
        `interface`: the generator params and default values
        `top_name`: the name of the top module
        `default_infiles` : a default list of .vp files to pass to genesis
        `system_verilog` : whether the top output file is system_verilog (.sv)
        `type_map`: mapping between port name to type that converts the
                    genesis/verilog port into a magma type, e.g.:
                    {"clk"      : m.In(m.Clock),
                     "reset"    : m.In(m.AsyncReset),
                     "config_en": m.In(m.Enable)}

        """
        self.__interface = interface
        self.__top_name = top_name
        self.__default_infiles = default_infiles
        self.__system_verilog = system_verilog
        self.__type_map = type_map

    def generator(self, param_mapping: Dict[str, str] = None,
                  mode: str = "define"):
        """
        `param_mapping`: (optional) a partial mapping between generator name and
            genesis name (used to rename parameters in the original genesis)
        """
        def define_wrapper(*args, **kwargs):
            if args:
                raise NotImplementedError(
                    "Currently only supports arguments passed explicity as "
                    "kwargs Ideally we'd support no kwargs, or partial ordered "
                    "args with kwargs. We would need to ensure they are "
                    "consistent")
            parameters = {}
            for param, (_, default) in self.__interface.params.items():
                if param_mapping is not None and param in param_mapping:
                    param = param_mapping[param]
                parameters[param] = kwargs.get(param, default)

            # Allow user to override default input_files
            infiles = kwargs.get("infiles", self.__default_infiles)

            outfile = run_genesis(self.__top_name, infiles, parameters,
                                  system_verilog=self.__system_verilog)
            if mode == "define":
                func = m.DefineFromVerilogFile
            elif mode == "declare":
                func = m.DeclareFromVerilogFile
            else:
                raise NotImplementedError(f"Unsupported mode '{mode}'")
            return func(outfile, type_map=self.__type_map)[0]

        return define_wrapper

    def parser(self):
        parser = argparse.ArgumentParser()
        for name, (type_, default) in self.__interface.params.items():
            parser.add_argument(f"--{name}", type=type_, default=default)
        parser.add_argument("infiles",
                            nargs="*",
                            default=self.__default_infiles)
        return parser

    def main(self, *, argv: List[str] = None,
             param_mapping: Dict[str, str] = None):
        define_wrapper = self.generator(param_mapping)
        parser = self.parser()
        args = parser.parse_args(argv)
        circuit = define_wrapper(**vars(args))
        print(circuit)
