# import paramiko
import os
import glob
import sys
import shutil

import generate_linker
import generate_app
import parse_gold

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

# copy tiles to tiles_chip_test
for i in range(num_tiles):
    shutil.copy(f"../SPARSE_TESTS/{app_name}_{app_name}-{data}_tile{i}/GLB_DIR/{app_name}_combined_seed_{app_name}-{data}_tile{i}/output_gold_0.npy", f"../SPARSE_TESTS/{app_name}_{app_name}-{data}_tile{i}/GLB_DIR/{app_name}_combined_seed_{app_name}-{data}_tile{i}/bin")
    shutil.copytree(f"../SPARSE_TESTS/{app_name}_{app_name}-{data}_tile{i}/GLB_DIR/{app_name}_combined_seed_{app_name}-{data}_tile{i}/bin", f"tiles_chip_test/tile{i}")

# combine tiles and generate C code
generate_app.gen_app(num_tiles, app_name, "sparse", ["tile0"])

# copy c code to dot_h_files
files = ["input_script.h", "script.h", "reg_write.h", "unrolling.h"]
if not os.path.exists(f"dot_h_files/{app_name}/{data}"):
    os.makedirs(f"dot_h_files/{app_name}/{data}")
for file in files:
    shutil.copy(file, f"dot_h_files/{app_name}/{data}/{app_name}_{data}_{file}")

# can we gold check?
if num_tiles <= 75:
    parse_gold.parse_gold(app_name, data)

# generate linker 
if generate_linker_flag == True:
    generate_linker.generate_linker("sections.ld", app_name)