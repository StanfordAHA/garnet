import magma
from gemstone.generator.const import Const
from gemstone.generator.generator import Generator
from hwtypes import BitVector
from collections import defaultdict
from gemstone.generator.port_reference import PortReferenceBase

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
                    #port_key = port.qualified_name()
                    port_key = hash(port)
                    connections_to_replace[port_key]['ext_intermediate'].append(port)
                    connections_to_replace[port_key]['external'].append(top_port)
        
        split_ports = set()
        for wire in inst.wires:
            for port in wire:
                print(f"name {port.qualified_name()} ops {len(port._ops)}")
                print(port._ops[0].index)
                if len(port._ops) == 0:
                    continue
                base_port = port.owner().ports[port._name]
                split_ports.add(base_port)
        print(split_ports)

        for wire in inst.wires:
            # Find any inst level wire connected to one of the insts ports
            for (ind, port) in enumerate(wire):
                if port.owner() == inst:
                    internal_port = wire[ind - 1]
                    #port_key = port.qualified_name()
                    port_key = hash(port)
                    connections_to_replace[port_key]['int_intermediate'].append(port)
                    if internal_port.owner() == inst:
                        # Handle pass through case here
                        internal_key = internal_port.qualified_name()
                        #internal_key = hash(internal_port)
                        external_dest = connections_to_replace[internal_key]['external']
                        connections_to_replace[port_key]['internal'] = external_dest
                        break
                    else:
                        if not (port_key in connections_to_replace):
                            print(f"{port.qualified_name()} NOT FOUND in inst {inst.name()}")
                            print(f"{port.owner().name()} NOT FOUND")
                            assert(False)
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
                inst.remove_wire(connection['int_intermediate'], internal)

        # Now reconnect everything 
        for connection in connections_to_replace.values():
            for external, ext_intermediate in zip(connection['external'], connection['ext_intermediate']:
                for internal, int_intermediate in zip(connection['internal'], connection['int_intermediate']):
                    # Use ops of the external and internal intermediate ports
                    # to handle split connections properly
                    top.wire(external, internal)

        print (connections_to_replace)
