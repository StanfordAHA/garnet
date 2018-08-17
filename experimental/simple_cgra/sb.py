import magma
from side_type import SideType
from configurable import Configurable
from mux_wrapper import MuxWrapper


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
        )
        for i, input_ in enumerate(self.all_inputs):
            self.add_port(f"core_out_{i}", input_.type())

        sides = (self.north, self.west, self.south, self.east)
        self.muxs = self.__make_muxs(sides)
        for (side, layer, track), mux in self.muxs.items():
            idx = 0
            for side_in in sides:
                if side_in == side:
                    continue
                mux_in = getattr(side.I, f"layer{layer}")[track]
                self.wire(mux_in, mux.I[idx])
                idx += 1
            for input_ in self.inputs[layer]:
                self.wire(input_, mux.I[idx])
                idx += 1
            mux_out = getattr(side.O, f"layer{layer}")[track]
            self.wire(mux.O, mux_out)

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

    def name(self):
        name = "SB"
        for input_ in self.all_inputs:
            name += "_" + str(input_.type())
        return name.replace("(", "$").replace(")", "$")
