import numpy as np
import os
import json

def concat_files(file1_path, file2_path, file3_path, output_file_path):
    try:
        with open(file1_path, 'rb') as file1, open(file2_path, 'rb') as file2, open(file3_path, 'rb') as file3:
            content1 = file1.read()
            content2 = file2.read()
            content3 = file3.read()

        with open(output_file_path, 'wb') as output_file:
            output_file.write(content1)
            output_file.write(content2)
            output_file.write(content3)

        print(f"Files {file1_path} and {file2_path} successfully concatenated to {output_file_path}")
    except Exception as e:
        print(f"Error: {str(e)}")

def add_extents(json_tile1, json_tile2, json_tile3):
    with open(json_tile1, "r") as f_tile1:
        tile1 = json.load(f_tile1)
    with open(json_tile2, "r") as f_tile2:
        tile2 = json.load(f_tile2)
    with open(json_tile3, "r") as f_tile3:
        tile3 = json.load(f_tile3)
    
    tile1_mode0_extents = tile1['IOs']["inputs"][0]["shape"] 
    tile1_mode1_extents = tile1['IOs']["inputs"][1]["shape"] 
    tile1_vals_extents = tile1['IOs']["inputs"][2]["shape"] 
    tile1_Cmode0_extents = tile1['IOs']["inputs"][3]["shape"]   
    tile1_Bmode_vals_extents = tile1['IOs']["inputs"][4]["shape"]
    tile1_Cmode_vals_extents = tile1['IOs']["inputs"][5]["shape"] 
    
    tile2_mode0_extents = tile2['IOs']["inputs"][0]["shape"]
    tile2_mode1_extents = tile2['IOs']["inputs"][1]["shape"]
    tile2_vals_extents = tile2['IOs']["inputs"][2]["shape"]
    tile2_Cmode0_extents = tile2['IOs']["inputs"][3]["shape"]
    tile2_Bmode_vals_extents = tile2['IOs']["inputs"][4]["shape"]
    tile2_Cmode_vals_extents = tile2['IOs']["inputs"][5]["shape"]

    tile3_mode0_extents = tile3['IOs']["inputs"][0]["shape"]
    tile3_mode1_extents = tile3['IOs']["inputs"][1]["shape"]
    tile3_vals_extents = tile3['IOs']["inputs"][2]["shape"]
    tile3_Cmode0_extents = tile3['IOs']["inputs"][3]["shape"]
    tile3_Bmode_vals_extents = tile3['IOs']["inputs"][4]["shape"]
    tile3_Cmode_vals_extents = tile3['IOs']["inputs"][5]["shape"]
    
    tile1_X_mode0_extents = tile1['IOs']["outputs"][0]["shape"]
    tile1_X_mode1_extents = tile1['IOs']["outputs"][1]["shape"]
    tile1_X_mode2_extents = tile1['IOs']["outputs"][2]["shape"]
    
    tile1_X_mode0_num_blocks = tile1['IOs']["outputs"][0]["io_tiles"][0]["num_blocks"]
    tile1_X_mode1_num_blocks = tile1['IOs']["outputs"][1]["io_tiles"][0]["num_blocks"]
    tile1_X_modevals_num_blocks = tile1['IOs']["outputs"][2]["io_tiles"][0]["num_blocks"]
    
    tile2_X_mode0_extents = tile2['IOs']["outputs"][0]["shape"]
    tile2_X_mode1_extents = tile2['IOs']["outputs"][1]["shape"]
    tile2_X_mode2_extents = tile2['IOs']["outputs"][2]["shape"]

    tile3_X_mode0_extents = tile3['IOs']["outputs"][0]["shape"]
    tile3_X_mode1_extents = tile3['IOs']["outputs"][1]["shape"]
    tile3_X_mode2_extents = tile3['IOs']["outputs"][2]["shape"]
    
    tile1_mode0_extents[0] += tile2_mode0_extents[0] + tile3_mode0_extents[0]
    tile1['IOs']["inputs"][0]["shape"] = tile1_mode0_extents
    tile1['IOs']["inputs"][0]["io_tiles"][0]["addr"]["extent"] = tile1_mode0_extents
    tile1_mode1_extents[0] += tile2_mode1_extents[0] + tile3_mode1_extents[0]
    tile1['IOs']["inputs"][1]["shape"] = tile1_mode1_extents
    tile1['IOs']["inputs"][1]["io_tiles"][0]["addr"]["extent"] = tile1_mode1_extents
    tile1_vals_extents[0] += tile2_vals_extents[0] + tile3_vals_extents[0]
    tile1['IOs']["inputs"][2]["shape"] = tile1_vals_extents
    tile1['IOs']["inputs"][2]["io_tiles"][0]["addr"]["extent"] = tile1_vals_extents
    tile1_Cmode0_extents[0] += tile2_Cmode0_extents[0] + tile3_Cmode0_extents[0]
    tile1['IOs']["inputs"][3]["shape"] = tile1_Cmode0_extents
    tile1['IOs']["inputs"][3]["io_tiles"][0]["addr"]["extent"] = tile1_Cmode0_extents
    tile1_Bmode_vals_extents[0] += tile2_Bmode_vals_extents[0] + tile3_Bmode_vals_extents[0]
    tile1['IOs']["inputs"][4]["shape"] = tile1_Bmode_vals_extents
    tile1['IOs']["inputs"][4]["io_tiles"][0]["addr"]["extent"] = tile1_Bmode_vals_extents
    tile1_Cmode_vals_extents[0] += tile2_Cmode_vals_extents[0] + tile3_Cmode_vals_extents[0]
    tile1['IOs']["inputs"][5]["shape"] = tile1_Cmode_vals_extents
    tile1['IOs']["inputs"][5]["io_tiles"][0]["addr"]["extent"] = tile1_Cmode_vals_extents
    
    tile1_X_mode0_num_blocks *= 3
    tile1['IOs']["outputs"][0]["io_tiles"][0]["num_blocks"] = tile1_X_mode0_num_blocks
    tile1_X_mode1_num_blocks *= 3
    tile1['IOs']["outputs"][1]["io_tiles"][0]["num_blocks"] = tile1_X_mode1_num_blocks
    tile1_X_modevals_num_blocks *= 3
    tile1['IOs']["outputs"][2]["io_tiles"][0]["num_blocks"] = tile1_X_modevals_num_blocks
    
    tile1_X_mode0_extents[0] += tile2_X_mode0_extents[0] + tile3_X_mode0_extents[0]
    tile1['IOs']["outputs"][0]["shape"] = tile1_X_mode0_extents
    tile1['IOs']["outputs"][0]["extents"] = tile1_X_mode0_extents
    tile1_X_mode1_extents[0] += tile2_X_mode1_extents[0] + tile3_X_mode1_extents[0]
    tile1['IOs']["outputs"][1]["shape"] = tile1_X_mode1_extents
    tile1['IOs']["outputs"][1]["extents"] = tile1_X_mode1_extents
    tile1_X_mode2_extents[0] += tile2_X_mode2_extents[0] + tile3_X_mode2_extents[0]
    tile1['IOs']["outputs"][2]["shape"] = tile1_X_mode2_extents
    tile1['IOs']["outputs"][2]["extents"] = tile1_X_mode2_extents
    
    json_string = json.dumps(tile1)
    f_tile1.close()
    new_f = open("temp.json", "w+")
    new_f.write(json_string)
    new_f.close()
    f_tile2.close()
    

app_name = "matmul_ijk"
dataset = "football"


# concat tile raw files together mode0, mode1, vals
concat_files(
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile0/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/tensor_B_mode_0.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile1/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile1/bin/tensor_B_mode_0.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile2/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile2/bin/tensor_B_mode_0.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile012/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/tensor_B_mode_0.raw")
concat_files(
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile0/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/tensor_C_mode_0.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile1/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile1/bin/tensor_C_mode_0.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile2/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile2/bin/tensor_C_mode_0.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile012/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/tensor_C_mode_0.raw")

concat_files(
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile0/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/tensor_B_mode_1.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile1/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile1/bin/tensor_B_mode_1.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile2/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile2/bin/tensor_B_mode_1.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile012/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/tensor_B_mode_1.raw")
concat_files(
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile0/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/tensor_C_mode_1.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile1/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile1/bin/tensor_C_mode_1.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile2/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile2/bin/tensor_C_mode_1.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile012/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/tensor_C_mode_1.raw")

concat_files(
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile0/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/tensor_B_mode_vals.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile1/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile1/bin/tensor_B_mode_vals.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile2/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile2/bin/tensor_B_mode_vals.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile012/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/tensor_B_mode_vals.raw")
concat_files(
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile0/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/tensor_C_mode_vals.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile1/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile1/bin/tensor_C_mode_vals.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile2/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile2/bin/tensor_C_mode_vals.raw",
 f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile012/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/tensor_C_mode_vals.raw")

# design_meta.json --> modify corresponding extents
# f = open(f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile0/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/design_meta.json")
# print(f.read())
tile0_design_meta = f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile0/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile0/bin/design_meta.json"
tile1_design_meta = f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile1/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile1/bin/design_meta.json"
tile2_design_meta = f"SPARSE_TESTS/{app_name}_{app_name}-{dataset}_tile2/GLB_DIR/{app_name}_combined_seed_{app_name}-{dataset}_tile2/bin/design_meta.json"
add_extents(tile0_design_meta, tile1_design_meta, tile2_design_meta)
