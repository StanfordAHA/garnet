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
                    connections_to_replace[port_key]['intermediate'] = port
                    connections_to_replace[port_key]['external'].append(top_port)

        for wire in inst.wires:
            # Find any inst level wire connected to one of the insts ports
            for (ind, port) in enumerate(wire):
                if port.owner() == inst:
                    internal_port = wire[ind - 1]
                    #port_key = port.qualified_name()
                    port_key = hash(port)
                    if internal_port.owner() == inst:
                        # Handle pass through case here
                        internal_key = hash(internal_port)
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
            intermediate = connection['intermediate']
            # Becuase of default dict, there is one  entry that's just empty. Skip this one
            if intermediate != []:
                #if not isinstance(intermediate, PortReferenceBase):
                #    print(intermediate) 
                # Break external connections
                for external in connection['external']:
                    top.remove_wire(intermediate, external)
                # Break internal connections
                for internal in connection['internal']:
                    inst.remove_wire(intermediate, internal)
            else:
                print(connection)
      
        # Now reconnect everything 
        for connection in connections_to_replace.values():
            for external in connection['external']:
                for internal in connection['internal']:
                    top.wire(external, internal)
