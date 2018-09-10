import magma as m


def check_interfaces(magma_circuit, genesis_circuit,
                     type_mapping={
                         "clk": m.ClockKind,
                         "reset": m.AsyncResetKind,
                         "config_en": m.EnableKind
                     }):
    """
    This checks that the interface to the genesis circuit is
    compatible with the magma circuit. It does that by looping
    over all the ports in the genesis circuit and checking that
    the magma circuit has the same port and type.

    It currently does not check the other direction (e.g. the magma circuit
    could have ports not included in the genesis circuit interface)

    `type_mapping` parameter allows the user to map genesis ports to a
    different type (by name). This reconciles differences between the generated
    verilog and the magma definition, e.g. for the ClockType, which doesn't
    exist in verilog.
    """
    genesis_port_names = genesis_circuit.interface.ports.keys()
    for name in genesis_port_names:
        assert hasattr(magma_circuit, name), \
            f"Magma circuit does not have port {name}"
        genesis_kind = type(type(getattr(genesis_circuit, name)))
        magma_kind = type(type(getattr(magma_circuit, name)))
        # Special case genesis signals that aren't typed
        if name in type_mapping:
            genesis_kind = type_mapping[name]
        assert issubclass(magma_kind, genesis_kind) or \
            issubclass(genesis_kind, magma_kind), "Types don't match"
