import magma as m


def check_interfaces(magma_circuit, genesis_circuit):
    """
    This checks that the interface to the genesis circuit is
    compatible with the magma circuit. It does that by looping
    over all the ports in the genesis circuit and checking that
    the magma circuit has the same port and type.

    It currently does not check the other direction (e.g. the magma circuit
    could have ports not included in the genesis circuit interface)
    """
    genesis_port_names = genesis_circuit.interface.ports.keys()
    for name in genesis_port_names:
        assert hasattr(magma_circuit, name), \
            f"Magma circuit does not have port {name}"
        genesis_kind = type(type(getattr(genesis_circuit, name)))
        magma_kind = type(type(getattr(magma_circuit, name)))
        # Special case genesis signals that aren't typed
        if name == "clk":
            genesis_kind = m.ClockKind
        elif name == "reset":
            genesis_kind = m.AsyncResetKind
        assert issubclass(magma_kind, genesis_kind) or \
            issubclass(genesis_kind, magma_kind), "Types don't match"
