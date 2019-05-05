import argparse
import magma
from canal.util import IOSide
from gemstone.common.configurable import ConfigurationType
from gemstone.common.jtag_type import JTAGType
from gemstone.common.testers import BasicTester
from gemstone.generator.generator import Generator
from global_controller.global_controller_magma import GlobalController
from global_controller.global_controller_wire_signal import\
    glc_interconnect_wiring
from global_buffer.global_buffer_magma import GlobalBuffer
from global_buffer.global_buffer_wire_signal import glb_glc_wiring, \
    glb_interconnect_wiring
from global_buffer.mmio_type import MMIOType
from global_controller.axi4_type import AXI4SlaveType
from canal.global_signal import GlobalSignalWiring
from mini_mapper import map_app
from cgra import create_cgra
import os
import math
import archipelago
import tempfile
import glob
import shutil


class Garnet(Generator):
    def __init__(self, width, height, add_pd, interconnect_only: bool = False):
        super().__init__()

        # configuration parameters
        config_addr_width = 32
        config_data_width = 32
        tile_id_width = 16
        config_addr_reg_width = 8
        num_tracks = 5

        # only north side has IO
        io_side = IOSide.North

        # global buffer parameters
        num_banks = 32
        bank_addr = 17
        bank_data = 64
        glb_addr = math.ceil(math.log2(num_banks)) + bank_addr

        # parallel configuration parameter
        num_parallel_cfg = math.ceil(width / 4)

        # number of input/output channels parameter
        num_io = math.ceil(width / 4)

        if not interconnect_only:
            wiring = GlobalSignalWiring.ParallelMeso
            self.global_controller = GlobalController(config_addr_width,
                                                      config_data_width)
            self.global_buffer = GlobalBuffer(num_banks=num_banks,
                                              num_io=num_io,
                                              num_cfg=num_parallel_cfg,
                                              bank_addr=bank_addr)
        else:
            wiring = GlobalSignalWiring.Meso

        interconnect = create_cgra(width, height, io_side,
                                   reg_addr_width=config_addr_reg_width,
                                   config_data_width=config_data_width,
                                   tile_id_width=tile_id_width,
                                   num_tracks=num_tracks,
                                   add_pd=add_pd,
                                   global_signal_wiring=wiring,
                                   num_parallel_config=num_parallel_cfg,
                                   mem_ratio=(1, 4))

        self.interconnect = interconnect

        if not interconnect_only:
            self.add_ports(
                jtag=JTAGType,
                clk_in=magma.In(magma.Clock),
                reset_in=magma.In(magma.AsyncReset),
                soc_data=MMIOType(glb_addr, bank_data),
                axi4_ctrl=AXI4SlaveType(config_addr_width, config_data_width),
            )

            # top <-> global controller ports connection
            self.wire(self.ports.clk_in, self.global_controller.ports.clk_in)
            self.wire(self.ports.reset_in,
                      self.global_controller.ports.reset_in)
            self.wire(self.ports.jtag, self.global_controller.ports.jtag)
            self.wire(self.ports.axi4_ctrl,
                      self.global_controller.ports.axi4_ctrl)

            # top <-> global buffer ports connection
            self.wire(self.ports.soc_data, self.global_buffer.ports.soc_data)
            glc_interconnect_wiring(self)
            glb_glc_wiring(self)
            glb_interconnect_wiring(self, width, num_parallel_cfg)
        else:
            # lift all the interconnect ports up
            for name in self.interconnect.interface():
                self.add_port(name, self.interconnect.ports[name].type())
                self.wire(self.ports[name], self.interconnect.ports[name])

            self.add_ports(
                clk=magma.In(magma.Clock),
                reset=magma.In(magma.AsyncReset),
                config=magma.In(
                    ConfigurationType(self.interconnect.config_data_width,
                                      self.interconnect.config_data_width)),
                stall=magma.In(
                    magma.Bits[self.interconnect.stall_signal_width]),
                read_config_data=magma.Out(magma.Bits[config_data_width])
            )

            self.wire(self.ports.clk, self.interconnect.ports.clk)
            self.wire(self.ports.reset, self.interconnect.ports.reset)

            self.wire(self.ports.config,
                      self.interconnect.ports.config)
            self.wire(self.ports.stall,
                      self.interconnect.ports.stall)

            self.wire(self.interconnect.ports.read_config_data,
                      self.ports.read_config_data)

    def map(self, halide_src):
        return map_app(halide_src)

    def get_placement_bitstream(self, placement, id_to_name, instrs):
        result = []
        for node, (x, y) in placement.items():
            instance = id_to_name[node]
            if instance not in instrs:
                continue
            instr = instrs[instance]
            result += self.interconnect.configure_placement(x, y, instr)
        return result

    def convert_mapped_to_netlist(self, mapped):
        raise NotImplemented()

    @staticmethod
    def get_input_output(netlist):
        inputs = []
        outputs = []
        for _, net in netlist.items():
            for blk_id, port in net:
                if port == "io2f_16":
                    inputs.append(blk_id)
                elif port == "f2io_16":
                    outputs.append(blk_id)
                elif port == "io2f_1":
                    inputs.append(blk_id)
                elif port == "f2io_1":
                    outputs.append(blk_id)
        return inputs, outputs

    def get_io_interface(self, inputs, outputs, placement):
        input_interface = []
        output_interface = []
        for blk_id in inputs:
            x, y = placement[blk_id]
            bit_width = 16 if blk_id[0] == "I" else 1
            name = f"glb2io_{bit_width}_X{x:02X}_Y{y:02X}"
            input_interface.append(name)
            assert name in self.interconnect.interface()
        for blk_id in outputs:
            x, y = placement[blk_id]
            bit_width = 16 if blk_id[0] == "I" else 1
            name = f"io2glb_{bit_width}_X{x:02X}_Y{y:02X}"
            output_interface.append(name)
            assert name in self.interconnect.interface()
        return input_interface, output_interface

    def compile(self, halide_src):
        id_to_name, instance_to_instr, netlist, bus = self.map(halide_src)
        placement, routing = archipelago.pnr(self.interconnect, (netlist, bus),
                                             cwd="temp")
        bitstream = []
        bitstream += self.interconnect.get_route_bitstream(routing)
        bitstream += self.get_placement_bitstream(placement, id_to_name,
                                                  instance_to_instr)
        inputs, outputs = self.get_input_output(netlist)
        input_interface, output_interface = self.get_io_interface(inputs,
                                                                  outputs,
                                                                  placement)
        return bitstream, (input_interface, output_interface)

    def name(self):
        return "Garnet"


def main():
    parser = argparse.ArgumentParser(description='Garnet CGRA')
    parser.add_argument('--width', type=int, default=4)
    parser.add_argument('--height', type=int, default=2)
    parser.add_argument("--input-app", type=str, default="", dest="app")
    parser.add_argument("--input-file", type=str, default="", dest="input")
    parser.add_argument("--gold-file", type=str, default="",
                        dest="gold")
    parser.add_argument("--delay", type=int, default=0)
    parser.add_argument("-v", "--verilog", action="store_true")
    parser.add_argument("--no-pd", "--no-power-domain", action="store_true")
    parser.add_argument("--interconnect-only", action="store_true")
    args = parser.parse_args()

    if not args.interconnect_only:
        assert args.width % 4 == 0 and args.width >= 4
    garnet = Garnet(width=args.width, height=args.height,
                    add_pd=not args.no_pd,
                    interconnect_only=args.interconnect_only)

    if args.verilog:
        garnet_circ = garnet.circuit()
        magma.compile("garnet", garnet_circ, output="coreir-verilog")
    if len(args.app) > 0:
        # do PnR and produce bitstream
        bitstream, (inputs, outputs) = garnet.compile(args.app)


if __name__ == "__main__":
    main()
