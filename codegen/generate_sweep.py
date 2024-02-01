import os
import glob
import sys
import shutil

import generate_linker
import generate_app
import parse_gold
import generate_main

# python3 generate_sweep.py <app_name> <data> 

#PARAMS
app_name = sys.argv[1]
data = sys.argv[2]

generate_linker_flag = True

# remove previously generated tiles
if os.path.exists("tiles_chip_test"):
    shutil.rmtree("tiles_chip_test")

# find tiles
tiles = glob.glob(f"../SPARSE_TESTS/{app_name}_{app_name}-{data}_tile*")
print(tiles)
num_tiles = len(tiles)
print("there are ", num_tiles, "tiles")


# folder naming
first_folder_name = f"{app_name}_{app_name}-{data}"
second_folder_name = f"{app_name}_combined_seed_{app_name}-{data}"

# first_folder_name = "tensor3_mttkrp_0"
# second_folder_name = "tensor3_mttkrp_combined_seed_0"
# num_tiles=1

# copy tiles to tiles_chip_test
for i in range(num_tiles):
    shutil.copy(f"../SPARSE_TESTS/{first_folder_name}_tile{i}/GLB_DIR/{second_folder_name}_tile{i}/output_gold_0.npy", f"../SPARSE_TESTS/{first_folder_name}_tile{i}/GLB_DIR/{second_folder_name}_tile{i}/bin")
    shutil.copytree(f"../SPARSE_TESTS/{first_folder_name}_tile{i}/GLB_DIR/{second_folder_name}_tile{i}/bin", f"tiles_chip_test/tile{i}")

# # cut tiles in half
# half_tiles = num_tiles // 2

# combine tiles and generate C code
tile_list = []
# TODO fix this for unroll=2 (use half_tiles and change append list to 2*tile/2*tile+1)
for tile in range(num_tiles):
    tile_list.append(f"tile{tile}")
inputs, outputs, input_order, output_order = generate_app.gen_app(num_tiles, app_name, "sparse", tile_list)
print(inputs, outputs, input_order, output_order)

# string replace reg_write.h for chip
reg_write = "reg_write.h"
with open(reg_write, 'r') as file:
    content = file.read()

# Replace glb_reg_write command for chip testing
modified_content = content.replace("glb_reg_write", "HAL_Cgra_Glb_WriteReg")
with open(reg_write, 'w') as file:
    file.write(modified_content)

# generate linker 
# inputs should be in order
if generate_linker_flag == True:
    generate_linker.generate_linker("sections.ld", app_name, inputs)

generate_main.generate_main(f"{app_name}_{data}", inputs, outputs)

# copy c code to dot_h_files
if os.path.exists(f"dot_h_files/{app_name}/{data}"):
    shutil.rmtree(f"dot_h_files/{app_name}/{data}")
    os.makedirs(f"dot_h_files/{app_name}/{data}")
else:
    os.makedirs(f"dot_h_files/{app_name}/{data}")
files = ["input_script.h", "script.h", "reg_write.h", "unrolling.h", "extents.h"]
for file in files:
    shutil.copy(file, f"dot_h_files/{app_name}/{data}/{app_name}_{data}_{file}")
files = ["main.c", "sections.ld"]
for file in files:
    shutil.copy(file, f"dot_h_files/{app_name}/{data}/{file}")

# can we gold check?
#if num_tiles <= 75:
#    parse_gold.parse_gold(app_name, data)

