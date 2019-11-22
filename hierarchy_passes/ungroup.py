import magma
from gemstone.generator.const import Const
from gemstone.generator.generator import Generator
from hwtypes import BitVector
from collections import defaultdict
from gemstone.generator.port_reference import PortReferenceBase

class PassThrough(Generator):
    def __init__(self, port_type, name):
        super().__init__()
        self.__name = name
        if (port_type == magma.In(magma.Bit)) or (port_type == magma.Out(magma.Bit)):
            T = magma.Bit
        else:
            T = magma.Bits[len(port_type)]
         
        self.add_ports(
            I=magma.In(T),
            O=magma.Out(T)
        )
        self.wire(self.ports.I, self.ports.O)

    def name(self):
        return self.__name
    
def get_external_connections(port: PortReferenceBase):
    external = []
    for conn in port._connections:
        if port.owner() != conn.owner():
            external.append(conn)
    return external
    

def ungroup(top: Generator, *insts):
    # If no insts are provided, ungroup all children
    if len(insts) == 0:
        insts = top.children()
    for inst in insts:
        # Dictionary of wires to remove keyed by inst port name
        connections_to_replace = defaultdict(lambda: defaultdict(list))
        pass_through_connections = set()
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
                    # check if either of the endpoints are split
                    if (len(port._ops) > 0) or (len(internal_port._ops) > 0):
                        connections_to_replace[port_key]['split'] = True
                    # Handle pass through case here
                    if internal_port.owner() == inst:
                        pass_through_connections.add(wire)
                    else:
                        connections_to_replace[port_key]['int_intermediate'].append(port)
                        connections_to_replace[port_key]['internal'].append(internal_port)

        # Handle the pass through connections
        pass_through_insts = []
        for (p1, p2) in pass_through_connections:
            if p1.type().isinput():
                in_port = p1
                out_port = p2
            else:
                in_port = p2
                out_port = p1
            # For all pass through connections, insert a PassThrough module (to be removed later)
            pass_through_inst = PassThrough(in_port.type(), "passthrough")
            inst.remove_wire(in_port, out_port)
            inst.wire(in_port, pass_through_inst.ports.I)
            inst.wire(out_port, pass_through_inst.ports.O)
            # Keep track of all the pass_through insts we insert here so we can clean them up later
            pass_through_insts.append(pass_through_inst)
            for port in (in_port, out_port):
                key = hash(port)
                connection = connections_to_replace[key]
                connection['int_intermediate'].append(port)
                if port == in_port:
                    connection['internal'].append(pass_through_inst.ports.I)
                else:
                    connection['internal'].append(pass_through_inst.ports.O)
        
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
            # Split connection
            if connection['split'] == True:
                print(f"Split connection detected for intermediate port {connection['int_intermediate'][0].qualified_name()}")
                intermediate = connection['ext_intermediate'][0]
                _port_combiner = PassThrough(intermediate.base_type(), f"splitport{intermediate.qualified_name()}")
                if intermediate.type().isinput():
                    external_combiner = _port_combiner.ports.I 
                    internal_combiner = _port_combiner.ports.O
                else:
                    external_combiner = _port_combiner.ports.O 
                    internal_combiner = _port_combiner.ports.I
                # Use ops of the external and internal intermediate ports
                # to handle split connections properly
                for external, ext_intermediate in zip(connection['external'], connection['ext_intermediate']):
                    intermediate = external_combiner
                    #intermediate._ops = []
                    for op in ext_intermediate._ops:
                        intermediate = op(intermediate)
                    top.wire(external, intermediate)
                for internal, int_intermediate in zip(connection['internal'], connection['int_intermediate']):
                    intermediate = internal_combiner
                    #intermediate._ops = []
                    for op in int_intermediate._ops:
                        intermediate = op(intermediate)
                    top.wire(internal, intermediate)
            # No split connection
            else:
                for external in connection['external']:
                    for internal in connection['internal']:
                        top.wire(external, internal)

        # Finally, clean up the PassThroughs
        for pass_through_inst in pass_through_insts:
            external_inputs = get_external_connections(pass_through_inst.ports.I)
            external_outputs = get_external_connections(pass_through_inst.ports.O)
            assert(len(external_inputs) == 1)
            assert(len(external_inputs) == len(external_outputs))
            # Bypass pass-through connection
            top.remove_wire(external_inputs[0], pass_through_inst.ports.I)
            top.remove_wire(external_outputs[0], pass_through_inst.ports.O)
            top.wire(external_inputs[0], external_outputs[0])
