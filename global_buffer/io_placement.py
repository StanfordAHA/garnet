import re
import os
import json
from canal.util import IOSide


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def parse_glb_bank_config(app_dir, id_to_name, inputs, mu_inputs, mu_io_tile_row, outputs, valid, placement):
    # Parse the glb_bank_config.json to specify bank locations
    with open(app_dir + "/glb_bank_config.json", "r") as f:
        glb_json = json.load(f)

    # Build input_coord_map {input_name: [x0, x1, …]} for inputs and mu_inputs
    input_coord_map = {}
    if "inputs" in glb_json:
        for item in glb_json.get("inputs", []):
            for name, data in item.items():
                input_coord_map[name] = data["x_coord"]
    # Build mu_input_coord_map {mu_input_name: [x0, x1, …]} for mu_inputs (if any)
    mu_input_coord_map = {}
    if "mu_inputs" in glb_json:
        for item in glb_json.get("mu_inputs", []):
            for name, data in item.items():
                mu_input_coord_map[name] = data["x_coord"]

    # Handling inputs
    if inputs:
        input_types = input_coord_map.keys()
        inputs_dict = {t: [] for t in input_types}
        index_counters = {t: 0 for t in input_types}
        for input_blk_id in inputs:
            input_blk_name = id_to_name[input_blk_id]
            type_name = next((t for t in input_types if t in input_blk_name), None)
            if type_name:
                idx = index_counters[type_name]
                coordinate = (input_coord_map[type_name][idx], 0)
                inputs_dict[type_name].append({input_blk_id: coordinate})
                index_counters[type_name] += 1

    # Handling mu_inputs (if any)
    if mu_inputs:
        mu_input_types = mu_input_coord_map.keys()
        mu_inputs_dict = {t: [] for t in mu_input_types}
        index_counters = {t: 0 for t in mu_input_types}
        for mu_input_blk_id in mu_inputs:
            mu_input_blk_name = id_to_name[mu_input_blk_id]
            type_name = next((t for t in mu_input_types if t in mu_input_blk_name), None)
            if type_name:
                idx = index_counters[type_name]
                coordinate = (mu_input_coord_map[type_name][idx], mu_io_tile_row)
                mu_inputs_dict[type_name].append({mu_input_blk_id: coordinate})
                index_counters[type_name] += 1

    # Build output_coord_map {output_name: [x0, x1, …]} for outputs
    output_coord_map = {}
    for item in glb_json["outputs"]:
        for name, data in item.items():
            output_coord_map[name] = data["x_coord"]

    # Handling outputs
    output_types = output_coord_map.keys()
    outputs_dict = {t: [] for t in output_types}
    index_counters = {t: 0 for t in output_types}
    for idx, output_blk_id in enumerate(outputs):
        output_blk_name = id_to_name[output_blk_id]
        type_name = next((t for t in output_types if t in output_blk_name), None)
        if type_name:
            idy = index_counters[type_name]
            coordinate = (output_coord_map[type_name][idy], 0)
            outputs_dict[type_name].append({output_blk_id: coordinate})
            if valid:
                outputs_dict[type_name].append({valid[idx]: coordinate})
            index_counters[type_name] += 1

    # Assert that all the inputs and outputs have been placed
    if inputs:
        assert sum(len(coords) for coords in inputs_dict.values()) == len(inputs), "Inputs in glb_bank_config.json do not match the number of inputs in the design"
    if mu_inputs:
        assert sum(len(coords) for coords in mu_inputs_dict.values()) == len(mu_inputs), "MU inputs in glb_bank_config.json do not match the number of mu inputs in the design"
    if valid:
        assert sum(len(coords) for coords in outputs_dict.values()) // 2 == len(outputs), "Outputs in glb_bank_config.json do not match the number of outputs in the design"
    else:
        assert sum(len(coords) for coords in outputs_dict.values()) == len(outputs), "Outputs in glb_bank_config.json do not match the number of outputs in the design"

    # Update the placement dictionary for inputs and outputs
    if inputs:
        for coord_list in inputs_dict.values():
            for coord_dict in coord_list:
                placement.update(coord_dict)
    for coord_list in outputs_dict.values():
        for coord_dict in coord_list:
            placement.update(coord_dict)

    return placement

def place_io_blk(id_to_name, app_dir, io_sides, orig_cgra_width, orig_cgra_height, mu_oc_0, num_fabric_cols_removed):
    """Hacky function to place the IO blocks"""

    if IOSide.West in io_sides:
        io_tile_shift_right_index = 1
    else:
        io_tile_shift_right_index = 0

    if os.getenv('WHICH_SOC') == "amber":
        blks = [blk for blk, _ in sorted(id_to_name.items(), key=lambda item: item[1])]

    else:
        # This is very hacky, if you change this sorting, the GLB scripts will break
        id_to_name_list = list(id_to_name.items())

        # Human sort thing from Kalhan used in GLB scripts
        id_to_name_list.sort(key=lambda x: natural_keys(x[1]))

        blks = [blk for (blk, _) in id_to_name_list]

    placement = {}
    # find out all the IO blocks
    ios = []
    inputs_from_MU = []
    for blk_id in blks:
        if blk_id[0] in {"i", "I"}:
            assert blk_id not in ios
            ios.append(blk_id)
        elif blk_id[0] in {"u", "U", "v", "V"}:
            assert blk_id not in inputs_from_MU
            inputs_from_MU.append(blk_id)

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

    # If operating in exchange_64 mode, place IOs in a denser way (4x denser)
    exchange_64_mode = "E64_MODE_ON" in os.environ and os.environ.get("E64_MODE_ON") == "1"

    # If operating in multi-bank mode, place IOs 8x denser and with all inputs placed first and then outputs
    multi_bank_mode = "E64_MULTI_BANK_MODE_ON" in os.environ and os.environ.get("E64_MULTI_BANK_MODE_ON") == "1"

    multi_bank_offset = 0
    if "MB_IO_OFFSET" in os.environ:
        multi_bank_offset = int(os.environ.get("MB_IO_OFFSET"))

    x_coord = -1
    group_index = 0
    for idx, input_blk in enumerate(inputs):
        if exchange_64_mode:
            if multi_bank_mode:
                x_coord = int((group_index * 2 ) / 8) + io_tile_shift_right_index + multi_bank_offset
            else:
                x_coord = int((group_index * 2 ) / 8) * 2 + io_tile_shift_right_index
            placement[input_blk] = (x_coord, 0)
        else:
            placement[input_blk] = (group_index * 2 + io_tile_shift_right_index, 0)
        group_index += 1
    for en_blk in en:
        placement[en_blk] = (group_index * 2 + io_tile_shift_right_index, 0)
        group_index += 1

    last_input_x_pos = multi_bank_offset-1 if len(inputs) == 0 else x_coord
    group_index = 0
    for idx, output_blk in enumerate(outputs):
        if exchange_64_mode:
            if multi_bank_mode:
                x_coord = int((group_index * 2 ) / 8) + last_input_x_pos + 1 + io_tile_shift_right_index
            else:
                x_coord = int((group_index * 2 ) / 8) * 2 + 1 + io_tile_shift_right_index
            placement[output_blk] = (x_coord, 0)
        else:
            placement[output_blk] = (group_index * 2 + 1 + io_tile_shift_right_index, 0)

        if idx < len(valid):
            placement[valid[idx]] = (group_index * 2 + 1 + io_tile_shift_right_index, 0)
        group_index += 1

    # place reset on the first one
    if reset is not None:
        #placement[reset] = (0, 0)
        placement[reset] = (1, 0)


    # Place MU I/O tiles if needed
    num_mu_io_tiles = int(mu_oc_0/2)
    mu_io_startX = int(((orig_cgra_width - num_fabric_cols_removed) - num_mu_io_tiles)/2) + num_fabric_cols_removed
    mu_io_tile_row = orig_cgra_height + 1

    for idx, input_blk in enumerate(inputs_from_MU):
        placement[input_blk] = (mu_io_startX + idx//2, mu_io_tile_row)

    # manual placement of PE/MEM tiles if needed
    resnet_manual_placer = "MANUAL_PLACER" in os.environ and os.environ.get("MANUAL_PLACER") == "1"
    path_balance_manual_placer = "MANUAL_PATH_BALANCE_PLACER" in os.environ and os.environ.get("MANUAL_PATH_BALANCE_PLACER") == "1"

    app_dir_pre_bin = app_dir.split("/bin")[0]

    if (resnet_manual_placer and os.path.isfile(app_dir + "/manual.place")) or (path_balance_manual_placer and os.path.isfile(app_dir_pre_bin + "/manual.place")):
        if path_balance_manual_placer:
            os.system(f"cp {app_dir_pre_bin}/manual.place {app_dir}/manual.place")
        with open(app_dir + "/manual.place", "r") as f:
            data = f.readlines()
            for dat in data:
                name, x, y = tuple(dat.split(" "))
                placement[name] = (x.strip(), y.strip())

    # parse the glb_bank_config.json to specify bank locations
    if os.path.isfile(app_dir + "/glb_bank_config.json"):
        placement = parse_glb_bank_config(app_dir, id_to_name, inputs, inputs_from_MU, mu_io_tile_row, outputs, valid, placement)

    return placement
