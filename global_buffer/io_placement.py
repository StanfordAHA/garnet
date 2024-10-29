import re
import os
import json


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]

def parse_glb_bank_config(app_dir, id_to_name, inputs, outputs, valid, placement):
    # parse the glb_bank_config.json to specify bank locations
    with open(app_dir + "/glb_bank_config.json", "r") as f:
        glb_json = json.load(f)

    # Handling inputs
    input_types = glb_json["inputs"].keys()
    inputs_dict = {input_type: [] for input_type in input_types}
    index_counters = {input_type: 0 for input_type in input_types}

    for input_blk_id in inputs:
        input_blk_name = id_to_name[input_blk_id]
        type_name = next((input_type for input_type in input_types if input_type in input_blk_name), None)
        if type_name:
            dict_idx = index_counters[type_name]
            coordinate = (glb_json["inputs"][type_name][dict_idx], 0)
            inputs_dict[type_name].append({input_blk_id: coordinate})
            index_counters[type_name] += 1

    # Handling outputs
    output_types = glb_json["outputs"].keys()
    outputs_dict = {output_type: [] for output_type in output_types}
    index_counters = {output_type: 0 for output_type in output_types}

    for idx, output_blk_id in enumerate(outputs):
        output_blk_name = id_to_name[output_blk_id]
        type_name = next((output_type for output_type in output_types if output_type in output_blk_name), None)
        if type_name:
            dict_idx = index_counters[type_name]
            coordinate = (glb_json["outputs"][type_name][dict_idx], 0)
            outputs_dict[type_name].append({output_blk_id: coordinate})
            outputs_dict[type_name].append({valid[idx]: coordinate})
            index_counters[type_name] += 1

    # Assert that all the inputs and outputs have been placed
    assert sum(len(coords) for coords in inputs_dict.values()) == len(inputs), "Inputs in glb_bank_config.json do not match the number of inputs in the design"
    assert sum(len(coords) for coords in outputs_dict.values()) // 2 == len(outputs), "Outputs in glb_bank_config.json do not match the number of outputs in the design"

    # Update the placement dictionary with input coordinates
    for type_name, coord_list in inputs_dict.items():
        for coord_dict in coord_list:
            for blk_id, coord in coord_dict.items():
                placement[blk_id] = coord

    # Update the placement dictionary with output coordinates
    for type_name, coord_list in outputs_dict.items():
        for coord_dict in coord_list:
            for blk_id, coord in coord_dict.items():
                placement[blk_id] = coord
    return placement

def place_io_blk(id_to_name, app_dir):
    """Hacky function to place the IO blocks"""

    if os.getenv('WHICH_SOC') == "amber":
        blks = [blk for blk, _ in sorted(id_to_name.items(), key=lambda item: item[1])]

    else:
        # This is very hacky, if you change this sorting, the GLB scripts will break
        #breakpoint()
        id_to_name_list = list(id_to_name.items())

        # Human sort thing from Kalhan used in GLB scripts
        id_to_name_list.sort(key=lambda x: natural_keys(x[1]))

        blks = [blk for (blk, _) in id_to_name_list]

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
        # Matrix unit hack 
        #placement[input_blk] = (group_index * 2, 0)
        placement[input_blk] = (group_index * 2 + 1, 0)
        group_index += 1
    for en_blk in en:
        #placement[en_blk] = (group_index * 2, 0)
        placement[en_blk] = (group_index * 2 + 1, 0)
        group_index += 1

    group_index = 0
    for idx, output_blk in enumerate(outputs):
        #placement[output_blk] = (group_index * 2 + 1, 0)
        placement[output_blk] = (group_index * 2 + 2, 0)
        if idx < len(valid):
            # placement[valid[idx]] = (group_index * 2 + 1, 0)
            placement[valid[idx]] = (group_index * 2 + 2, 0)
        group_index += 1

    # place reset on the first one
    if reset is not None:
        #placement[reset] = (0, 0)
        placement[reset] = (1, 0)

    # manual placement of PE/MEM tiles if needed
    if os.path.isfile(app_dir + "/manual.place"):
        with open(app_dir + "/manual.place", "r") as f:
            data = f.readlines()
            for dat in data:
                name, x, y = tuple(dat.split(" "))
                placement[name] = (x.strip(), y.strip())

    # parse the glb_bank_config.json to specify bank locations
    if os.path.isfile(app_dir + "/glb_bank_config.json"):
        placement = parse_glb_bank_config(app_dir, id_to_name, inputs, outputs, valid, placement)

    return placement
