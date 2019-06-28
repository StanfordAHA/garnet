def place_io_blk(id_to_name, width):
    """Hacky function to place the IO blocks"""
    placement = {}
    # find out all the IO blocks
    ios = []
    for blk_id in id_to_name:
        if blk_id[0] in {"i", "I"}:
            assert blk_id not in ios
            ios.append(blk_id)

    # make it deterministic
    ios.sort()

    # need to know if it's an input or output

    reset = None
    valid = None
    en = []

    for blk_id in ios:
        if "reset" in id_to_name[blk_id]:
            reset = blk_id
        elif "in_en" in id_to_name[blk_id]:
            en.append(blk_id)
        elif "valid" in id_to_name[blk_id]:
            valid = blk_id

    if reset is not None:
        ios.remove(reset)
    if valid is not None:
        ios.remove(valid)
    for sig in en:
        ios.remove(sig)

    # need to find out if it's an input or output
    inputs = []
    outputs = []
    for blk_id in ios:
        if "in" in id_to_name[blk_id]:
            inputs.append(blk_id)
        else:
            assert "out" in id_to_name[blk_id]
            outputs.append(blk_id)

    # place it on the interconnect
    group_index = 0
    for idx, input_blk in enumerate(inputs):
        placement[input_blk] = (group_index * 4, 0)
        if idx < len(en):
            placement[en[idx]] = (group_index * 4, 0)
        group_index += 1

    for output_blk in outputs:
        placement[output_blk] = (group_index * 4 + 1, 0)
        if valid is not None:
            placement[valid] = (group_index * 4 + 1, 0)
        group_index += 1

    # place reset on the last one
    if reset is not None:
        placement[reset] = (width - 1, 0)

    return placement
