# script to convert bitstream to h file

import json


def meta_scrape(meta_file_name):

    f = open(meta_file_name)
    meta = json.load(f)

    input_files = []
    input_order_list = []
    output_files = []
    output_order_list = []


    # inputs 
    for input in meta["IOs"]["inputs"]:
        input_files.append(input["datafile"])
        input_order = []
        for io in input["io_tiles"]:
            input_order.append(io["x_pos"] // 2)
        input_order_list.append(input_order)

    # outputs
    for output in meta["IOs"]["outputs"]:
        output_files.append(output["datafile"])
        output_order = []
        for io in output["io_tiles"]:
            output_order.append(io["x_pos"] // 2)
        output_order_list.append(output_order)

    return input_files, output_files, input_order_list, output_order_list,  meta["testing"]["bitstream"]

    


if __name__ == '__main__':
    inputs, outputs, input_order, output_order, bitstream = meta_scrape(meta_file_name)