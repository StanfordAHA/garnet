# import paramiko
import os
import pexpect
import glob
import sys

import generate_linker
import generate_app

# python3 generate_sweep.py <app_name> <data> 

#PARAMS
app_name = sys.argv[1]
data = sys.argv[2]

generate_linker_flag = False
### 

empty_local = f"rm -rf ../tiles_chip_test"
print(empty_local)
os.system(empty_local)

empty_local = f"rm -rf tiles_chip_test"
print(empty_local)
os.system(empty_local)

os.chdir("../SPARSE_TESTS")
rm_tiles = "rm -rf tile*"
os.system(rm_tiles)

os.system(f"python3 generate_tile_files.py {app_name} {data}")
os.chdir("../codegen")

num_tile_dirs = glob.glob("tiles_chip_test/tile*")
num_tile = len(num_tile_dirs)

print("There are " + str(num_tile) + " tiles")

generate_app.gen_app(num_tile, app_name, "sparse", ["tile0"])

files = ["input_script.h", "script.h", "reg_write.h", "unrolling.h"]

if not os.path.exists(f"dot_h_files/{app_name}/{data}"):
    os.makedirs(f"dot_h_files/{app_name}/{data}")

for file in files:
    cp_to_my_workspace = f"cp {file} dot_h_files/{app_name}/{data}/{app_name}_{data}_{file}"
    print(cp_to_my_workspace)
    os.system(cp_to_my_workspace)

if num_tile <= 75:
    print("we can do automated gold check")
    parse_gold = f"python3 parse_gold.py {app_name} {data}"
    print(parse_gold)
    os.system(parse_gold)

if generate_linker_flag == True:
    generate_linker.generate_linker("sections.ld", app_name)
