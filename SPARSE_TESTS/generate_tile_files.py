import shutil
import glob
import subprocess
import os

app_name = "mat_elemmul"

tiles = glob.glob(f"./{app_name}_tile*")

print(tiles)
num_tiles = len(tiles)
print("there are ", num_tiles, "tiles")

for i in range(num_tiles):
    shutil.copy(f"{app_name}_tile{i}/GLB_DIR/{app_name}_combined_seed_tile{i}/output_gold_0.npy", f"{app_name}_tile{i}/GLB_DIR/{app_name}_combined_seed_tile{i}/bin")
    shutil.copytree(f"{app_name}_tile{i}/GLB_DIR/{app_name}_combined_seed_tile{i}/bin", f"/aha/garnet/SPARSE_TESTS/tile{i}")


# for tile in tiles:
#     shutil.copy(f"{tile}/GLB_DIR/{tile[:12]}_combined_seed{tile[12:]}/output_gold_0.npy", f"{tile}/GLB_DIR/{tile[:12]}_combined_seed{tile[12:]}/bin")
#     shutil.copytree(f"{tile}/GLB_DIR/{tile[:12]}_combined_seed{tile[12:]}/bin", f"/aha/garnet/SPARSE_TESTS/{tile[13:]}")

# Get a list of all tile directories
tile_directories = glob.glob("tile*")

# Create the destination directory if it doesn't exist
destination_dir = "../tiles_chip_test"
os.makedirs(destination_dir, exist_ok=True)

# Move the tile directories to the destination directory
for tile_dir in tile_directories:
    destination_path = os.path.join(destination_dir, tile_dir)
    shutil.move(tile_dir, destination_path)
