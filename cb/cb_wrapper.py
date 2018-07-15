from common.genesis_wrapper import define_genesis_generator

define_cb_wrapper = define_genesis_generator(
    top_name="cb",
    input_files=["cb.vp"],
    width=16,
    num_tracks=10,
    feedthrough_outputs="1111101111",
    has_constant=1,
    default_value=0
)
