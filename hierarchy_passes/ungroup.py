import magma
from gemstone.generator.const import Const
from gemstone.generator.generator import Generator
from hwtypes import BitVector
from collections import defaultdict
from gemstone.generator.port_reference import PortReferenceBase

class PortCombiner(Generator):
    def __init__(self, old_port):
        super().__init__()
        self.old_port = old_port
        width = len(old_port.base_type())
        self.add_ports(
            I=magma.In(magma.Bits[width]),
            O=magma.Out(magma.Bits[width])
        )
        self.wire(self.ports.I, self.ports.O)

    def name(self):
        return f"{self.old_port.qualified_name()}_combiner"
    

def ungroup(top: Generator, *insts):
    # If no insts are provided, ungroup all children
    if len(insts) == 0:
        insts = top.children()
    for inst in insts:
        # Dictionary of wires to remove keyed by inst port name
        connections_to_replace = defaultdict(lambda: defaultdict(list))
        for wire in top.wires:
            # Find any top level wire that goes to the inst we want to ungroup
            for (ind, port) in enumerate(wire):
                if port.owner() == inst:
                    top_port = wire[ind - 1]
                    port_key = hash(port)
                    # check if either of the endpoints are split
                    if (len(port._ops) > 0) or (len(top_port._ops) > 0):
                        connections_to_replace[port_key]['split'] = True
                    connections_to_replace[port_key]['ext_intermediate'].append(port)
                    connections_to_replace[port_key]['external'].append(top_port)
        
        # Find any inst level wire connected to one of the insts ports
        for wire in inst.wires:
            for (ind, port) in enumerate(wire):
                if port.owner() == inst:
                    internal_port = wire[ind - 1]
                    port_key = hash(port)
                    connections_to_replace[port_key]['int_intermediate'].append(port)
                    # check if either of the endpoints are split
                    if (len(port._ops) > 0) or (len(internal_port._ops) > 0):
                        connections_to_replace[port_key]['split'] = True
                    # Handle pass through case here
                    if internal_port.owner() == inst:
                        pass_through_key = hash(internal_port)
                        external_dest = connections_to_replace[pass_through_key]['external']
                        connections_to_replace[port_key]['internal'].extend(external_dest)
                        break
                    else:
                        connections_to_replace[port_key]['internal'].append(internal_port)
        
        # Now replace all (external <-> intermediate) and (intermediate <-> internal) connections
        # with (external <-> internal) connections
        # First break the connections
        for connection in connections_to_replace.values():
            # Break external connections
            for external, intermediate in zip(connection['external'], connection['ext_intermediate']):
                top.remove_wire(intermediate, external)
            # Break internal connections
            for internal, intermediate in zip(connection['internal'], connection['int_intermediate']):
                inst.remove_wire(intermediate, internal)

        # Now reconnect everything 
        for connection in connections_to_replace.values():
            assert(len(connection['external']) == len(connection['ext_intermediate']))
            assert(len(connection['internal']) == len(connection['int_intermediate']))
            if connection['split'] == True:
                print(f"Split connection detected for intermediate port {connection['int_intermediate'][0].qualified_name()}")
                intermediate = connection['ext_intermediate'][0]
                _port_combiner = PortCombiner(intermediate)
                if intermediate.base_type().isinput():
                    external_combiner = _port_combiner.ports.I 
                    internal_combiner = _port_combiner.ports.O
                else:
                    external_combiner = _port_combiner.ports.O 
                    internal_combiner = _port_combiner.ports.I
                # Use ops of the external and internal intermediate ports
                # to handle split connections properly
                for external, ext_intermediate in zip(connection['external'], connection['ext_intermediate']):
                    intermediate = external_combiner
                    intermediate._ops = []
                    for op in ext_intermediate._ops:
                        intermediate = op(intermediate)
                    top.wire(external, intermediate)
                    print("doing external split port stuff")
                
                for internal, int_intermediate in zip(connection['internal'], connection['int_intermediate']):
                    intermediate = internal_combiner
                    intermediate._ops = []
                    for op in int_intermediate._ops:
                        intermediate = op(intermediate)
                    top.wire(internal, intermediate)
                    print("doing internal split port stuff")
            else:
                for external in connection['external']:
                    for internal in connection['internal']:
                        top.wire(external, internal)
