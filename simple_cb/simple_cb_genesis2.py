from common.genesis_wrapper import GenesisWrapper, default_type_map
from common.generator_interface import GeneratorInterface


interface = GeneratorInterface()\
    .register("width", int, 16)\
    .register("num_tracks", int, 10)

simple_cb_wrapper = GenesisWrapper(
    interface,
    "simple_cb",
    ["simple_cb/genesis/simple_cb.vp"],
    type_map=default_type_map)

if __name__ == "__main__":
    # These functions are unit tested directly, so no need to cover them
    simple_cb_wrapper.main()  # pragma: no cover
