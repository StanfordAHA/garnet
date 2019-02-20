from gemstone.common.genesis_wrapper import GenesisWrapper
from gemstone.common.generator_interface import GeneratorInterface


interface = GeneratorInterface()\
    .register("width", int, 16)\
    .register("num_tracks", int, 2)\
    .register("sides", int, 4)\
    .register("feedthrough_outputs", str, "00")\
    .register("registered_outputs", str, "11")\
    .register("pe_output_count", int, 1)\
    .register("is_bidi", int, 0)\
    .register("sb_fs", str, "10#10#10")

sb_wrapper = GenesisWrapper(interface, "sb", ["sb/genesis/sb.vp"])

if __name__ == "__main__":
    # These functions are unit tested directly, so no need to cover them
    sb_wrapper.main()  # pragma: no cover
