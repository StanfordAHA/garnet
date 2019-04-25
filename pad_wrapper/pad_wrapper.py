import magma
from gemstone.generator.generator import Generator
from gemstone.generator.const import Const
from gemstone.generator.from_verilog import FromVerilog
import os


class Pad(Generator):
    def __init__(self, is_input, is_vertical):
        super().__init__()
        self.is_input = is_input
        self.is_vertical = is_vertical
        if self.is_input:
            pad_type = magma.In(magma.Bit)
            fabric_type = magma.Out(magma.Bit)
        else:
            pad_type = magma.Out(magma.Bit)
            fabric_type = magma.In(magma.Bit)
        self.add_ports(
            pad=pad_type,
            fabric=fabric_type,
            rte=magma.In(magma.Bit)
        )

        pad_verilog_file = "pad_wrapper/verilog_stubs/pad_stub"
        if self.is_vertical:
            pad_verilog_file += "_v_"
        else:
            pad_verilog_file += "_h_"
        if self.is_input:
            pad_verilog_file += "in.v"
        else:
            pad_verilog_file += "out.v"
        

        self.pad = FromVerilog(pad_verilog_file)
        # Wire up input/output/control signals to pad
        self.wire(self.ports.pad, self.pad.ports.PAD)
        self.wire(Const(magma.Bit(self.is_input)), self.pad.ports.IE)
        self.wire(Const(magma.Bit(self.is_input)), self.pad.ports.OEN)
        self.wire(self.ports.rte, self.pad.ports.RTE)
        if self.is_input:
            self.wire(self.ports.fabric, self.pad.ports.C)
            self.wire(Const(magma.Bit(0)), self.pad.ports.I)
        else:
            self.wire(self.ports.fabric, self.pad.ports.I)

        # Other random signals we need to hook up
        self.wire(Const(magma.Bit(0)), self.pad.ports.ST)
        self.wire(Const(magma.Bit(0)), self.pad.ports.SL)
        self.wire(Const(magma.Bit(0)), self.pad.ports.DS0)
        self.wire(Const(magma.Bit(0)), self.pad.ports.DS1)
        self.wire(Const(magma.Bit(0)), self.pad.ports.DS2)
        self.wire(Const(magma.Bit(0)), self.pad.ports.PU)
        self.wire(Const(magma.Bit(0)), self.pad.ports.PD)


    def compile(self):
        raise NotImplementedError()

    def name(self):
        pad_name = "pad_"
        if self.is_input:
            pad_name += "in_"
        else:
            pad_name += "out_"
        if self.is_vertical:
            pad_name += "v"
        else:
            pad_name += "h"
        
        return pad_name 
