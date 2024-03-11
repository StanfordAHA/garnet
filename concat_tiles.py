import numpy as np
import json
import sys
import os
import subprocess

def concat_files(input_files, output_file_path):
    contents = []
    assert len(input_files) > 0
    try:
        str_stream = ""
        for file_path in input_files:
            with open(file_path, 'rb') as file:
                contents.append(file.read())
            str_stream += file_path + " "

        with open(output_file_path, 'wb') as output_file:
            for content in contents:
                output_file.write(content)

        # print(f"Files {str_stream} successfully concatenated to {output_file_path}")
    except Exception as e:
        print(f"Error: {str(e)}")

def add_extents(json_tiles, output_file_path):

    tiles = []
    for json_tile in json_tiles:
        with open(json_tile, "r") as f_tile:
            tile = json.load(f_tile)
            tiles.append(tile)

    num_input = len(tiles[0]['IOs']["inputs"])
    num_output = len(tiles[0]['IOs']["outputs"])

    for i in range(num_input):
        # print(i)
        tile_base = tiles[0]['IOs']["inputs"][i]["shape"]
        # print(tile_base[0])
        for j in range(1, len(tiles)):
            tile_base[0] += tiles[j]['IOs']["inputs"][i]["shape"][0]
            # print(tiles[j]['IOs']["inputs"][i]["shape"][0])
        tiles[0]['IOs']["inputs"][i]["shape"] = tile_base
        # print(tile_base[0])
        tiles[0]['IOs']["inputs"][i]["io_tiles"][0]["addr"]["extent"] = tile_base

    for i in range(num_output):
        tiles[0]['IOs']["outputs"][i]["io_tiles"][0]["num_blocks"] *= len(tiles)

    for i in range(num_output):
        tile_base = tiles[0]['IOs']["outputs"][i]["shape"]
        for j in range(1, len(tiles)):
            tile_base[0] += tiles[j]['IOs']["outputs"][i]["shape"][0]
        tiles[0]['IOs']["outputs"][i]["shape"] = tile_base
        tiles[0]['IOs']["outputs"][i]["extents"] = tile_base
    
    json_string = json.dumps(tiles[0])
    new_f = open(output_file_path, "w+")
    new_f.write(json_string)
    new_f.close()

def create_concate(app_name = "matmul_ijk", dataset = "football", tiles = [0, 1]):
    base_dir_list = []
    for tile in tiles:
        base_dir_list.append(f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile{tile}/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile{tile}/bin/")
    
    output_tile = ""
    for tile in tiles:
        output_tile += f"_t{tile}"
    
    output_base_dir = f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile{output_tile}/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile{output_tile}/bin/"

    t_base = "/aha/garnet/"
    if os.path.exists(t_base + f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile{output_tile}"):
        subprocess.run(["rm", "-rf", t_base + f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile{output_tile}"])

    subprocess.run(["cp", "-rf", t_base + f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile{tiles[0]}/", t_base + f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile{output_tile}/"])
    output_base_dir_s = t_base + f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile{output_tile}/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile{output_tile}"
    output_base_dir_s_pre = t_base + f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile{output_tile}/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile{tiles[0]}"
    subprocess.run(["mv", output_base_dir_s_pre, output_base_dir_s])

    design_meta = base_dir_list[0] + "design_meta.json"
    with open(design_meta, "r") as f_tile:
        meta_f = json.load(f_tile)
        f_tile.close()

    input_t_num = len(meta_f['IOs']["inputs"])
    input_files = []
    for i in range(input_t_num):
        input_files.append(meta_f['IOs']["inputs"][i]["datafile"])
        # print(meta_f['IOs']["inputs"][i]["datafile"])
    
    # concat input files
    for input_file in input_files:
        i_f = []
        o_f_path = output_base_dir + input_file
        for base_dir in base_dir_list:
            i_f.append(base_dir + input_file)
        concat_files(i_f, o_f_path)

    meta_files = []
    for base_dir in base_dir_list:
        meta_files.append(base_dir + "design_meta.json")
    o_f_path = output_base_dir + "design_meta.json"
    add_extents(meta_files, o_f_path)

    # this one is without bin folder
    base_dir_list = []
    for tile in tiles:
        base_dir_list.append(f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile{tile}/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile{tile}/")
    gold_files = []
    for base_dir in base_dir_list:
        gold_files.append(t_base + base_dir + "output_gold_0.npy")
    
    output_base_dir = f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile{output_tile}/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile{output_tile}/"
    for i in range(len(gold_files)):
        subprocess.run(["cp", gold_files[i],t_base + output_base_dir + f"output_gold_{i}.npy"])

if __name__ == "__main__":
    # parse input
    if len(sys.argv) != 3: # run with internal modification
        create_concate()
    else:
        assert len(sys.argv) == 3
        app_name = sys.argv[1]
        dataset = sys.argv[2]
        create_concate(app_name, dataset)
