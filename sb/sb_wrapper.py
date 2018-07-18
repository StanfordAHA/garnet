from common.genesis_wrapper import define_genesis_generator

define_sb_wrapper = define_genesis_generator(
    top_name="sb",
    input_files=["sb.vp"],
    width=16,
    num_tracks=2,
    sides=4,
    feedthrough_outputs="00",
    registered_outputs="11",
    pe_output_count=1,
    is_bidi=0,
    sb_fs="10#10#10" 
)
