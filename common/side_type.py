import magma


def SideType(num_tracks, layers):
    layers_dict = {f"layer{l}": magma.Array(num_tracks, magma.Bits(l))
                   for l in layers}
    T = magma.Tuple(**layers_dict)
    return magma.Tuple(I=magma.In(T), O=magma.Out(T))
