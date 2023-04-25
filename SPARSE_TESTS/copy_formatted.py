import shutil
import glob
import subprocess
import os

b_tensors = glob.glob("../matmul_ijk_ch7-6-b1/formatted/tensor_B*")
c_tensors = glob.glob("../matmul_ijk_ch7-6-b1/formatted/tensor_C*")

os.system("rm -rf ./matmul*")
os.system("rm -rf ./MAT_TMP_DIR/tile*")

tile = 0

print(b_tensors)

for b in b_tensors:
    for c in c_tensors:
        tile_str = "tile" + str(tile)
        b_loc = b[-7:]
        c_loc = c[-7:]
        b_loc = b_loc.split("_")
        c_loc = c_loc.split("_")
        if(b_loc[1] == c_loc[0] and b_loc[3] == c_loc[2]):
            print(b, c)
            if not os.path.exists(f"./MAT_TMP_DIR/{tile_str}"):
                os.mkdir(f"./MAT_TMP_DIR/{tile_str}")
            shutil.copy(f"{b}/B0_crd.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
            shutil.copy(f"{b}/B0_seg.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

            shutil.copy(f"{b}/B1_crd.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
            shutil.copy(f"{b}/B1_seg.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

            shutil.copy(f"{b}/B_vals.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

            shutil.copy(f"{b}/B_shape.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

            shutil.copy(f"{c}/C0_crd.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
            shutil.copy(f"{c}/C0_seg.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

            shutil.copy(f"{c}/C1_crd.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
            shutil.copy(f"{c}/C1_seg.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

            shutil.copy(f"{c}/C_vals.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

            shutil.copy(f"{c}/C_shape.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

            # subprocess.call(["aha",
            #     "regress",
            #     "fast"],
            #     text=True)

            # shutil.copy("/aha/garnet/SPARSE_TESTS/GLB_DIR/matmul_ijk_combined_seed_tile1/output_gold.npy", "/aha/garnet/SPARSE_TESTS/GLB_DIR/matmul_ijk_combined_seed_tile1/bin")
            # shutil.copytree("/aha/garnet/SPARSE_TESTS/GLB_DIR/matmul_ijk_combined_seed_tile1/bin", f"/aha/garnet/SPARSE_TESTS/{tile_str}")
            tile = tile + 1



