import numpy as np
import os
import json

app_name = "mat_elemadd"
def concat_files(file1_name, file2_name, new_file_name):
    with open(file1_name, "r") as file1:
        lines1 = file1.readlines()

    with open(file2_name, "r") as file2:
        lines2 = file2.readlines()

    combined_lines = lines1 + lines2

    with open(new_file_name, "w") as combined_file:
        combined_file.writelines(combined_lines)

def add_extents(json_tile1, json_tile2):
    with open(json_tile1, "r") as f_tile1:
        tile1 = json.load(f_tile1)
    with open(json_tile2, "r") as f_tile2:
        tile2 = json.load(f_tile2)
    
    tile1_mode0_extents = tile1['IOs']["inputs"][0]["shape"]
    tile1_mode1_extents = tile1['IOs']["inputs"][1]["shape"]
    tile1_vals_extents = tile1['IOs']["inputs"][2]["shape"]
    # tile1_mode0_num_blocks = tile1['IOs']["inputs"][0]["io_tiles"][0]["num_blocks"]
    
    tile2_mode0_extents = tile2['IOs']["inputs"][0]["shape"]
    tile2_mode1_extents = tile2['IOs']["inputs"][1]["shape"]
    tile2_vals_extents = tile2['IOs']["inputs"][2]["shape"]
    # tile2_mode0_num
    
    tile1_X_mode0_extents = tile1['IOs']["outputs"][0]["shape"]
    tile1_X_mode1_extents = tile1['IOs']["outputs"][1]["shape"]
    tile1_X_mode2_extents = tile1['IOs']["outputs"][2]["shape"]
    
    tile1_X_mode0_num_blocks = tile1['IOs']["outputs"][0]["io_tiles"][0]["num_blocks"]
    tile1_X_mode1_num_blocks = tile1['IOs']["outputs"][1]["io_tiles"][0]["num_blocks"]
    
    tile2_X_mode0_extents = tile2['IOs']["outputs"][0]["shape"]
    tile2_X_mode1_extents = tile2['IOs']["outputs"][1]["shape"]
    tile2_X_mode2_extents = tile2['IOs']["outputs"][2]["shape"]
    
    tile1_mode0_extents[0] += tile2_mode0_extents[0]
    tile1['IOs']["inputs"][0]["shape"] = tile1_mode0_extents
    tile1['IOs']["inputs"][0]["io_tiles"][0]["addr"]["extent"] = tile1_mode0_extents
    tile1_mode1_extents[0] += tile2_mode1_extents[0]
    tile1['IOs']["inputs"][1]["shape"] = tile1_mode1_extents
    tile1['IOs']["inputs"][1]["io_tiles"][0]["addr"]["extent"] = tile1_mode0_extents
    tile1_vals_extents[0] += tile2_vals_extents[0]
    tile1['IOs']["inputs"][2]["shape"] = tile1_vals_extents
    tile1['IOs']["inputs"][2]["io_tiles"][0]["addr"]["extent"] = tile1_vals_extents
    
    tile1_X_mode0_num_blocks *= 2
    tile1['IOs']["outputs"][0]["io_tiles"][0]["num_blocks"] = tile1_X_mode0_num_blocks
    tile1_X_mode1_num_blocks *= 2
    tile1['IOs']["outputs"][1]["io_tiles"][0]["num_blocks"] = tile1_X_mode1_num_blocks
    
    tile1_X_mode0_extents += tile2_X_mode0_extents
    tile1['IOs']["outputs"][0]["shape"] = tile1_X_mode0_extents
    tile1['IOs']["outputs"][0]["extents"] = tile1_X_mode0_extents
    tile1_X_mode1_extents += tile2_X_mode1_extents
    tile1['IOs']["outputs"][1]["shape"] = tile1_X_mode1_extents
    tile1['IOs']["outputs"][1]["extents"] = tile1_X_mode1_extents
    tile1_X_mode2_extents += tile2_X_mode2_extents
    tile1['IOs']["outputs"][2]["shape"] = tile1_X_mode2_extents
    tile1['IOs']["outputs"][2]["extents"] = tile1_X_mode1_extents
    
    json_string = json.dumps(tile1)
    f_tile1.close()
    new_f = open("temp.json", "w+")
    new_f.write(json_string)
    new_f.close()
    f_tile2.close()
    
         
# concat tile raw files together mode0, mode1, vals
concat_files(f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/tensor_B_mode_0.raw", f"SPARSE_TESTS/{app_name}_tile1/GLB_DIR/{app_name}_combined_seed_tile1/bin/tensor_B_mode_0.raw", f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/tensor_B_mode_0.raw")
concat_files(f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/tensor_C_mode_0.raw", f"SPARSE_TESTS/{app_name}_tile1/GLB_DIR/{app_name}_combined_seed_tile1/bin/tensor_C_mode_0.raw", f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/tensor_C_mode_0.raw")

concat_files(f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/tensor_B_mode_1.raw", f"SPARSE_TESTS/{app_name}_tile1/GLB_DIR/{app_name}_combined_seed_tile1/bin/tensor_B_mode_1.raw", f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/tensor_B_mode_1.raw")
concat_files(f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/tensor_C_mode_1.raw", f"SPARSE_TESTS/{app_name}_tile1/GLB_DIR/{app_name}_combined_seed_tile1/bin/tensor_C_mode_1.raw", f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/tensor_C_mode_1.raw")

concat_files(f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/tensor_B_mode_vals.raw", f"SPARSE_TESTS/{app_name}_tile1/GLB_DIR/{app_name}_combined_seed_tile1/bin/tensor_B_mode_vals.raw", f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/tensor_B_mode_vals.raw")
concat_files(f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/tensor_C_mode_vals.raw", f"SPARSE_TESTS/{app_name}_tile1/GLB_DIR/{app_name}_combined_seed_tile1/bin/tensor_C_mode_vals.raw", f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/tensor_C_mode_vals.raw")

# design_meta.json --> modify corresponding extents
# f = open(f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/design_meta.json")
# print(f.read())
tile0_design_meta = f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/bin/design_meta.json"
tile1_design_meta = f"SPARSE_TESTS/{app_name}_tile1/GLB_DIR/{app_name}_combined_seed_tile1/bin/design_meta.json"
add_extents(tile0_design_meta, tile1_design_meta)
# f = open
# data_tile0 = json.load(f)
# print(data_tile0)
# mode0 = data_tile0['IOs']["inputs"][0]
# mode0_extents = mode0["shape"] # AND EXTENTS
# mode1 = data_tile0['IOs']["inputs"][1]
# mode1_extents = mode1["shape"] # AND EXTENTS
# print(data_tile0['IOs']["outputs"][0]["shape"])
# X_mode0 = data_tile0['IOs']['outputs'][0]
# X_mode0_extents = X_mode0["shape"]
# X_mode1 = data_tile0['IOs']['outputs'][1]
# X_mode1_extents = X_mode1["shape"]

# new output_gold.npy --> need 2, one for each tile and to compare