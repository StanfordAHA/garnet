from common.genesis_wrapper import GenesisWrapper
from common.generator_interface import GeneratorInterface


"""
Defines the pad frame using genesis2.

`config_data_width`: Number of bits in configuration data
`config_addr_width`: Number of bits in configuration address
`num_ios_per_group`: Number of io1bit tiles in each io_group
`num_groups_per_side`: Number of groups on each of the 4 sides
`tile_id_offset`: ID we begin counting from to assign
                  ids to each io1bit tile. Will probably get
                  rid of this once we develop configuration manager

Example usage:
    >>> pad_frame = pad_frame_wrapper.generator()(
            config_data_width=32, config_addr_width=32,
            num_ios_per_group=16, num_groups_per_side=1,
            tile_id_offset=400)
"""
interface = GeneratorInterface()\
            .register("num_ios_per_group", int, 16)\
            .register("num_groups_per_side", int, 1)\
            .register("config_addr_width", int, 32)\
            .register("config_data_width", int, 32)\
            .register("tile_id_offset", int, 400)

pad_frame_wrapper = GenesisWrapper(
    interface, "pad_frame", ["pad_frame/genesis/pad_frame.vp",
                             "pad_frame/genesis/io_group.vp",
                             "pad_frame/genesis/io1bit.vp"])

if __name__ == "__main__":
    """
    This program generates the verilog for the pad frame and parses it into a
    Magma circuit. The circuit declaration is printed at the end of the
    program.
    """
    # These functions are unit tested directly, so no need to cover them
    pad_frame_wrapper.main()  # pragma: no cover
