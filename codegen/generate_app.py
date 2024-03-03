import sys
import shutil
import json
import os

import io_placement
import raw_to_h_16
import bs_to_h
import meta


def gen_app(num_tiles, app_name, type_of_app, name_list):
    import json

    import io_placement
    import raw_to_h_16
    import bs_to_h
    import meta
    
    # for dense use the single app, for sparse we use the concatenation of inputs
    if type_of_app == "dense":
        dense = 1
        data_file_str = name_list[0] + "/"
    else:
        dense = 0
        data_file_str = "./"

    # Get input/output file name information, io order and bitstream from first tile
    inputs, outputs, input_order, output_order, bitstream_name = meta.meta_scrape(f"tiles_chip_test/tile0/design_meta.json")

    # bitstream is same for every tile
    path = name_list[0]
    first_tile_path = f"tiles_chip_test/tile0/"

    bs_to_h.convert_bs(f"{first_tile_path}{bitstream_name}", f"tiles_chip_test/tile0/")

    # copy reg_write and script into base folder
    shutil.copy(f"{first_tile_path}reg_write.h", "./")
    shutil.copy(f"{first_tile_path}script.h", "./")


    # need to generate image input/output per tile
    # combine inputs into one raw file
    if not dense: 
        input_paths = []
        for input_file in inputs:
            for name in name_list:
                input_paths.append(f"{name}/{input_file}")
            with open(input_file, "wb") as output:
                for file in input_paths:
                    file = "tiles_chip_test/" + file
                    with open(file, "rb") as partial:
                        shutil.copyfileobj(partial, output)
                    # length = (1024*2 - os.path.getsize(file)) / 2
                    # for i in range(int(length)):
                    #     output.write(b'\x00\x00')

            input_paths = []


    # get extents of all inputs
    # initialize dict
    extent_dict = {}
    for input in inputs:
        extent_dict[input] = []


    for name in name_list:
        meta_file_name = f"tiles_chip_test/{name}/design_meta.json"
        f = open(meta_file_name)
        meta = json.load(f)

        # add extents
        for input in meta["IOs"]["inputs"]:
            extent_dict[input["datafile"]].append(input["shape"][0])


    # convert to input
    raw_to_h_16.convert_image(inputs, outputs, data_file_str, len(name_list), dense)

    # io placement and extents
    io_placement.unrolling(inputs, outputs, input_order, output_order, extent_dict, name_list, dense, app_name)

    return inputs, outputs, input_order, output_order

if __name__ == "main":
    gen_app(num_tiles, app_name, type_of_app, name_list)