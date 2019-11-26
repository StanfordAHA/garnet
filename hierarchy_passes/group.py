import magma
from gemstone.generator.generator import Generator


class _GroupWrapper(Generator):
    def __init__(self, name, instances, prefixes=None):
        super().__init__()

        self.__name = name
        self.instances = instances
        self.port_map = {}
        if prefixes is None:
            prefixes = [f"Inst{i}_" for i in range(len(self.instances))]
        for i, inst in enumerate(self.instances):
            prefix = prefixes[i]
            for key, port in inst.ports.items():
                new_key = f"{prefix}{key}"
                self.add_port(new_key, port.type())
                self.wire(port, self.ports[new_key])
                self.port_map[port] = self.ports[new_key]

    def name(self):
        return self.__name


class _GeneratorBuilder(Generator):
    def __init__(self, name=None):
        super().__init__()

        self.__name = name

    def name(self):
        return self.__name

    def set_name(self, name):
        self.__name = name


def _get_external(wire, insts):
    port0, port1 = wire
    if port0.owner() in insts and port1.owner() not in insts:
        return (port1, port0)
    if port1.owner() in insts and port0.owner() not in insts:
        return (port0, port1)
    return None


def group(top: Generator, group_name, *insts):
    children = top.children().copy()
    assert all(inst in children for inst in insts)
    wrapper = _GeneratorBuilder(name=group_name)
    top_wires = top.wires.copy()
    removed_wires = []
    removed_internal_wires = []
    for top_wire in top_wires:
        sorted_ = _get_external(top_wire, insts)
        if sorted_ is None:
            port0, port1 = top_wire
            if port0.owner() in insts and port1.owner() in insts:
                top.remove_wire(port0, port1)
                removed_internal_wires.append((port0, port1))
            continue
        external, internal = sorted_
        top.remove_wire(external, internal)
        removed_wires.append((external, internal))
    counter = 0
    removed_wires_sorted = sorted(removed_wires, key=lambda x: hash(x[1]))
    for external, internal in removed_wires_sorted:
        new_port_name = f"port{counter}"
        counter += 1
        wrapper.add_port(new_port_name, internal.type())
        wrapper.wire(internal, wrapper.ports[new_port_name])
        top.wire(wrapper.ports[new_port_name], external)
    for port0, port1 in removed_internal_wires:
        wrapper.wire(port0, port1)
    return wrapper
