import json
import numpy as np

# json_file = "temp.json"

json_file = "SPARSE_TESTS/mat_elemadd_tile0/GLB_DIR/mat_elemadd_combined_seed_tile0/bin/design_meta.json"

with open(json_file, "r") as f_tile1:
    tile = json.load(f_tile1)
print("tile, mode0, shape : ", tile['IOs']["inputs"][0]["shape"])
    
print("tile, mode1, shape : ", tile['IOs']["inputs"][1]["shape"])
print("tile, vals, shape : ", tile['IOs']["inputs"][2]["shape"])

print("tile, mode0, extents : ", tile['IOs']["inputs"][0]["io_tiles"][0]["addr"]["extent"])
print("tile, mode1, extents : ", tile['IOs']["inputs"][1]["io_tiles"][0]["addr"]["extent"])
print("tile, vals, extents : ", tile['IOs']["inputs"][2]["io_tiles"][0]["addr"]["extent"])

gold1 = "SPARSE_TESTS/mat_elemadd_tile0/GLB_DIR/mat_elemadd_combined_seed_tile0/output_gold_0.npy"
gold2 = "SPARSE_TESTS/mat_elemadd_tile1/GLB_DIR/mat_elemadd_combined_seed_tile1/output_gold_0.npy"

arr1 = np.load(gold1)
arr2 = np.load(gold2)

result = np.vstack((arr1, arr2))
print(result)