from common.mux_with_default import MuxWithDefaultWrapper
from generator.from_magma import FromMagma
from generator.generator import Generator
import magma
import mantle


def pass_signal_through(gen: Generator, signal):
    """Takes in an existing input of the tile and creates and output
       to pass the signal through
       returns the new output port reference
    """
    pass_through = None
    if signal in gen.ports.values():
        pass_through = signal
    elif signal in gen.ports.keys():
        pass_through = gen.ports[signal]
    assert pass_through is not None, "Cannot find " + pass_through
    # Create output port for pass through
    output_name = pass_through.qualified_name() + "_out"
    gen.add_port(output_name, magma.Out(pass_through.base_type()))
    # Actually make the pass through connection
    gen.wire(pass_through, gen.ports[output_name])
    return gen.ports[output_name]


def or_reduction(gen: Generator, sub_circuit_name: str, signal_name: str,
                 config_data_width: int,
                 sub_circuit_port_name: str = "O"):
    """Embeds @signal_name reduction network in tile by accepting a @signal_name
       input from another tile and ORing it with the origin @@signal_name
       output of this tile to create a new read_data output.

        @signal_name has to be connected to @sub_circuit_name
    """
    pass_through = gen.ports[signal_name]
    input_name = pass_through.qualified_name() + "_in"
    # Create input port for pass through @signal_name reduction
    gen.add_port(input_name, magma.In(pass_through.base_type()))
    # get the sub circuit
    sub_circuit = getattr(gen, sub_circuit_name)
    # Remove the current connection to the @signal_name output
    gen.remove_wire(sub_circuit.ports[sub_circuit_port_name], pass_through)
    read_data_reduce_or = FromMagma(mantle.DefineOr(2, config_data_width))
    # OR previous read_data output with @signal_name input to create NEW
    # @signal_name output
    gen.wire(sub_circuit.ports[sub_circuit_port_name],
             read_data_reduce_or.ports.I0)
    gen.wire(gen.ports[input_name], read_data_reduce_or.ports.I1)
    gen.wire(read_data_reduce_or.ports.O, pass_through)

    return gen.ports[input_name]
