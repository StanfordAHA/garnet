def place_io_blk(id_to_name):
    """Hacky function to place the IO blocks"""

    blks = [blk for blk, _ in sorted(id_to_name.items(), key=lambda item: item[1])]

    placement = {}
    # find out all the IO blocks
    ios = []
    for blk_id in blks:
        if blk_id[0] in {"i", "I"}:
            assert blk_id not in ios
            ios.append(blk_id)


    # need to know if it's an input or output

    reset = None
    valid = []
    en = []

    for blk_id in ios:
        if "reset" in id_to_name[blk_id]:
            reset = blk_id
        elif "in_en" in id_to_name[blk_id]:
            en.append(blk_id)
        elif "valid" in id_to_name[blk_id]:
            valid.append(blk_id)

    if reset is not None:
        ios.remove(reset)
    for sig in valid:
        ios.remove(sig)
    for sig in en:
        ios.remove(sig)

    # need to find out if it's an input or output
    inputs = []
    outputs = []
    for blk_id in ios:
        if "output" in id_to_name[blk_id]:
            assert "write" in id_to_name[blk_id]
            outputs.append(blk_id)
        else:
            assert "read" in id_to_name[blk_id]
            inputs.append(blk_id)

    # place it on the interconnect
    # input and outputs are placed on the same IO tiles
    group_index = 0
    for idx, input_blk in enumerate(inputs):
        placement[input_blk] = (group_index * 2, 0)
        group_index += 1
    for en_blk in en:
        placement[en_blk] = (group_index * 2, 0)
        group_index += 1

    group_index = 0
    for idx, output_blk in enumerate(outputs):
        placement[output_blk] = (group_index * 2 + 1, 0)
        if idx < len(valid):
            placement[valid[idx]] = (group_index * 2 + 1, 0)
        group_index += 1

    # place reset on the first one
    if reset is not None:
        placement[reset] = (0, 0)

    return placement
