import functools
import magma as m


def _flatten(bag):
    try:
        iter(bag)
    except:
        return [bag]
    return [a for i in bag for a in _flatten(i)]


def _get_inst(value):
    ref = value.name
    if isinstance(ref, m.InstRef):
        return ref.inst
    if isinstance(ref, m.ArrayRef):
        return _get_inst(ref.array)
    if isinstance(ref, m.TupleRef):
        return _get_inst(ref.tuple)
    raise NotImplementedError(value, ref)


def _find(defn, name, seed=None):
    ret = False
    if seed is None:
        ret = True
        seed = []
    instances = getattr(defn, "instances", [])
    for inst in instances:
        if inst.name == name:
            seed += [inst]
        _find(type(inst), name, seed)
    if ret:
        return seed
    return


def _driving(port):
    if isinstance(port, m.Digital):
        return [d.bit for d in port._wire.driving]
    if isinstance(port, m.Array):
        return [_driving(t) for t in port]
    raise NotImplementedError()


def _get_connected(port):
    if port.is_input():
        value = _flatten(port.value())
        return set(_get_inst(v) for v in value)
    if port.is_output():
        value = _flatten(_driving(port))
        return set(_get_inst(v) for v in value)
    raise NotImplementedError(port)


def _is_mux(inst):
    defn = type(inst)
    return defn.name[0:4] == "Mux2"


def _data_gate_inst(inst):
    out_insts = _get_connected(inst.O)
    if len(out_insts) == 0 or not all(map(_is_mux, out_insts)):
        print ("SKIPPING", inst)
        return
    selects = [inst.S.value() for inst in out_insts]
    assert all(isinstance(s, m.Bit) for s in selects)

    print (inst)

    a = inst.I0.value()
    b = inst.I1.value()
    if a is None or b is None:
        print ("SKIPPING", inst)
        return

    print ("DOING", inst)
    defn = inst.defn
    with defn.open():
        select = selects[0]
        for s in selects[1:]:
            select = select | s
        inst.I0.unwire(a)
        inst.I1.unwire(b)
        inst.I0 @= a & m.bits(len(a) * [select])
        inst.I1 @= b & m.bits(len(b) * [select])


def data_gate(pe):
    names = ("magma_BFloat_16_mul_inst0",
             "magma_Bits_16_mul_inst0",
             "magma_Bits_32_mul_inst0",)
    insts = []
    for name in names:
        insts += _find(pe, name)
    for inst in insts:
        _data_gate_inst(inst)
