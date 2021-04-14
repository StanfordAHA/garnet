import functools
import operator
import lassen
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


def _get_connected(port):
    if port.is_input():
        value = _flatten(port.value())
        return set(_get_inst(v) for v in value)
    if port.is_output():
        value = _flatten(port.driving())
        return set(_get_inst(v) for v in value)
    raise NotImplementedError(port)


def _is_mux(inst):
    defn = type(inst)
    return defn.name[0:4] == "Mux2"


def _data_gate_inst(inst, make_gate=None):
    if make_gate is None:

        def make_gate(_):
            out_insts = _get_connected(inst.O)
            if len(out_insts) == 0 or not all(map(_is_mux, out_insts)):
                return None
            selects = [inst.S.value() for inst in out_insts]
            assert all(isinstance(s, m.Bit) for s in selects)
            return functools.reduce(operator.or_, selects[1:], selects[0])

    a = inst.I0.value()
    b = inst.I1.value()
    if a is None or b is None:
        return

    defn = inst.defn
    with defn.open():
        gate = make_gate(defn)
        if gate is None:
            return
        assert isinstance(gate, m.Bit)
        inst.I0.unwire(a)
        inst.I1.unwire(b)
        inst.I0 @= a & m.bits(len(a) * [gate])
        inst.I1 @= b & m.bits(len(b) * [gate])


def data_gate(pe):

    # NOTE(rsetaluri): This is hardcoded!
    def _make_bits_16_mul_gate(defn):
        op = defn.alu
        return ((op == lassen.alu.ALU_t.FCnvExp2F) |
                (op == lassen.alu.ALU_t.FCnvInt2F))

    expensive = (("magma_BFloat_16_mul_inst0", None),
                 ("magma_BFloat_16_add_inst0", None),
                 ("magma_UInt_16_mul_inst0", _make_bits_16_mul_gate),
                 ("magma_UInt_32_mul_inst0", None),)

    for name, make_gate in expensive:
        insts = _find(pe, name)
        for inst in insts:
            _data_gate_inst(inst, make_gate=make_gate)
