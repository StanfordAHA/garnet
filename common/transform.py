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


def read_data_reduction(gen):
    """Embeds read_data reduction network in tile by accepting a read_data
       input from another tile and ORing it with the origin read_data
       output of this tile to create a new read_data output
    """
    pass_through = gen.ports.read_config_data
    input_name = pass_through.qualified_name() + "_in"
    # Create input port for pass through read_data reduction
    gen.add_port(input_name, magma.In(pass_through.base_type()))
    # Remove the current connection to the read_data output
    gen.remove_wire(gen.read_data_mux.ports.O, pass_through)
    gen.read_data_reduce_or = FromMagma(mantle.DefineOr(2, 32))
    # OR previous read_data output with read_data input to create NEW
    # read_data output
    gen.wire(gen.read_data_mux.ports.O,
             gen.read_data_reduce_or.ports.I0)
    gen.wire(gen.ports[input_name], gen.read_data_reduce_or.ports.I1)
    gen.wire(gen.read_data_reduce_or.ports.O, pass_through)
