import shutil
import glob
import subprocess
import os

tiles = glob.glob("./matmul_ijk_tile*")

print(tiles)
for tile in tiles:
    shutil.copy(f"{tile}/GLB_DIR/{tile[:12]}_combined_seed{tile[12:]}/output_gold.npy", f"{tile}/GLB_DIR/{tile[:12]}_combined_seed{tile[12:]}/bin")
    shutil.copytree(f"{tile}/GLB_DIR/{tile[:12]}_combined_seed{tile[12:]}/bin", f"/aha/garnet/SPARSE_TESTS/{tile[13:]}")

 