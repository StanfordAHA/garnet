import magma


def SideType(num_tracks, layers):
    layers_dict = {f"layer{l}" : magma.Bits(l) for l in layers}
    LayersType = magma.Tuple(**layers_dict)
    T = magma.Array(num_tracks, LayersType)
    return magma.Tuple(I=magma.In(T), O=magma.Out(T))


