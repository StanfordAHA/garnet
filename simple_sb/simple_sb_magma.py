import magma
from common.side_type import SideType
from generator.configurable import Configurable, ConfigurationType
from common.mux_wrapper import MuxWrapper
from common.zext_wrapper import ZextWrapper
from mantle import DefineRegister
from generator.from_magma import FromMagma


def get_width(T):
    if isinstance(T, magma._BitKind):
        return 1
    if isinstance(T, magma.BitsKind):
        return T.N
    raise NotImplementedError(T, type(T))


class SB(Configurable):
    def __init__(self, inputs):
        super().__init__()

        self.all_inputs = inputs
        self.inputs = self.__organize_inputs(inputs)

        self.add_ports(
            north=SideType(5, (1, 16)),
            west=SideType(5, (1, 16)),
            south=SideType(5, (1, 16)),
            east=SideType(5, (1, 16)),
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            config=magma.In(ConfigurationType(8, 32)),
            read_config_data=magma.Out(magma.Bits(32)),
        )

        # TODO(rsetaluri): Clean up this logic.
        for i, input_ in enumerate(self.all_inputs):
            assert input_.type().isoutput()
            port_name = f"{input_._name}"
            self.add_port(port_name, magma.In(input_.type()))

        sides = (self.ports.north, self.ports.west,
                 self.ports.south, self.ports.east)
        self.muxs = self.__make_muxs(sides)
        for (side, layer, track), mux in self.muxs.items():
            idx = 0
            for side_in in sides:
                if side_in == side:
                    continue
                mux_in = getattr(side_in.I, f"layer{layer}")[track]
                self.wire(mux_in, mux.ports.I[idx])
                idx += 1
            for input_ in self.inputs[layer]:
                port_name = input_._name
                self.wire(self.ports[port_name], mux.ports.I[idx])
                idx += 1
            buffered_mux = self.__make_register_buffer(mux)
            mux_out = getattr(side.O, f"layer{layer}")[track]
            self.wire(buffered_mux.ports.O, mux_out)

            # Add corresponding config register.
            config_name = f"mux_{side._name}_{layer}_{track}"
            config_name_mux = config_name + '_sel'
            config_name_buffer = config_name + '_buffer_sel'
            self.add_config(config_name_mux, mux.sel_bits)
            self.wire(self.registers[config_name_mux].ports.O, mux.ports.S)
            self.add_config(config_name_buffer, buffered_mux.sel_bits)
            self.wire(self.registers[config_name_buffer].ports.O,
                      buffered_mux.ports.S)

        # NOTE(rsetaluri): We set the config register addresses explicitly and
        # in a well-defined order. This ordering can be considered a part of
        # the functional spec of this module.
        idx = 0
        for side in sides:
            for layer in (1, 16):
                for track in range(5):
                    reg_name = f"mux_{side._name}_{layer}_{track}"
                    reg_name_mux = reg_name + '_sel'
                    reg_name_buffer = reg_name + '_buffer_sel'
                    self.registers[reg_name_mux].set_addr(idx)
                    idx += 1
                    self.registers[reg_name_buffer].set_addr(idx)
                    idx += 1

        for idx, reg in enumerate(self.registers.values()):
            reg.set_addr_width(8)
            reg.set_data_width(32)
            self.wire(self.ports.config.config_addr, reg.ports.config_addr)
            self.wire(self.ports.config.config_data, reg.ports.config_data)
            self.wire(self.ports.config.write[0], reg.ports.config_en)
            self.wire(self.ports.reset, reg.ports.reset)

        # read_config_data output
        num_config_reg = len(self.registers)
        if(num_config_reg > 1):
            self.read_config_data_mux = MuxWrapper(num_config_reg, 32)
            sel_bits = self.read_config_data_mux.sel_bits
            # Wire up config_addr to select input of read_data MUX
            # TODO(rsetaluri): Make this a mux with default.
            self.wire(self.ports.config.config_addr[:sel_bits],
                      self.read_config_data_mux.ports.S)
            self.wire(self.read_config_data_mux.ports.O,
                      self.ports.read_config_data)
            for idx, reg in enumerate(self.registers.values()):
                zext = ZextWrapper(reg.width, 32)
                self.wire(reg.ports.O, zext.ports.I)
                zext_out = zext.ports.O
                self.wire(zext_out, self.read_config_data_mux.ports.I[idx])
        # If we only have 1 config register, we don't need a mux
        # Wire sole config register directly to read_config_data_output
        else:
            self.wire(self.registers[0].ports.O, self.ports.read_config_data)

    def __organize_inputs(self, inputs):
        ret = {1: [], 16: []}
        for input_ in inputs:
            width = get_width(input_.type())
            assert width == 1 or width == 16
            ret[width].append(input_)
        return ret

    def __make_muxs(self, sides):
        height_per_layer = {
            1: 3 + len(self.inputs[1]),
            16: 3 + len(self.inputs[16]),
        }
        muxs = {}
        for side in sides:
            for layer, height in height_per_layer.items():
                for track in range(5):
                    muxs[(side, layer, track)] = MuxWrapper(height, layer)
        return muxs

    def __make_register_buffer(self, unbuffered_mux):
        signal_in = unbuffered_mux.ports.O
        width = get_width(signal_in.type())

        # register = Register(width)
        RegisterCls = DefineRegister(width)
        register = FromMagma(RegisterCls)

        mux = MuxWrapper(2, width)
        self.wire(signal_in, mux.ports.I[0])
        self.wire(signal_in, register.ports.I)
        self.wire(register.ports.O, mux.ports.I[1])
        return mux

    def name(self):
        name = "SB"
        for input_ in self.all_inputs:
            name += "_" + str(input_.type())
        return name.replace("(", "_").replace(")", "_")
