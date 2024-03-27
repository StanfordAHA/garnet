import json
import sys
import subprocess
import scipy
import os
import numpy as np
from sam.onyx.generate_matrices import MatrixGenerator, get_tensor_from_files

app_name = sys.argv[1]
data = sys.argv[2]

with open("tiles_accumulation.json", "r") as file:
    tiles_accumulation = json.load(file)

print(tiles_accumulation)

if not os.path.exists(f"output_matrix/{app_name}/{data}"):
    os.makedirs(f"output_matrix/{app_name}/{data}")

for k, v in tiles_accumulation.items():
    print(k, v)

    gold_matrix = np.load(f"SPARSE_TESTS/{app_name}_tile0/GLB_DIR/{app_name}_combined_seed_tile0/output_gold_0.npy")
    output_matrix = np.zeros(gold_matrix.shape)
    for tile in v:
        # run aha glb on tile
        subprocess.call(["aha", 
                "glb", 
                f"../../../garnet/SPARSE_TESTS/{app_name}_{tile}/GLB_DIR/{app_name}_combined_seed_{tile}",  
                "--sparse", 
                "--sparse-test-name", 
                f"{app_name}", 
                "--sparse-comparison", 
                f"/aha/garnet/SPARSE_TESTS/{app_name}_{tile}/GLB_DIR/{app_name}_combined_seed_{tile}/"],
                text=True)

        #reconstruct output matrix
        output_name = "X"
        gold_matrix = np.load(f"SPARSE_TESTS/{app_name}_{tile}/GLB_DIR/{app_name}_combined_seed_{tile}/output_gold_0.npy")
        sim_matrix = get_tensor_from_files(name=output_name, files_dir="/aha/garnet/SPARSE_TESTS/",
                                            format="CSF",
                                            shape=gold_matrix.shape, base=16, early_terminate='x')
        sim_matrix_np = sim_matrix.get_matrix()

        #add output matrices
        output_matrix += sim_matrix_np

    # save output_matrix
    scipy.io.mmwrite(f"output_matrix/{app_name}/{data}/output_matrix_{k}.mtx", output_matrix)
