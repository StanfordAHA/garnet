import shutil
import glob
import os
import sys

# test = "rel5" 
# test = "mk9-b1"
# test = "fb1k"
app_name = sys.argv[1]
test = sys.argv[2]
# app_name = "mat_mattransmul"
# app_name = "tensor3_elemadd"

const_val = 2 # only for mat_mattransmul

b_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}/{app_name}/{test}/formatted/tensor_B*")
c_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}/{app_name}/{test}/formatted/tensor_C*")
d_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}/{app_name}/{test}/formatted/tensor_D*")

# b_tensors = glob.glob(f"/aha/garnet/tiles/{app_name}/{test}/formatted/tensor_B*")
# c_tensors = glob.glob(f"/aha/garnet/tiles/{app_name}/{test}/formatted/tensor_C*")
# d_tensors = glob.glob(f"/aha/garnet/tiles/{app_name}/{test}/formatted/tensor_D*")

# print("b_tensors: ", b_tensors)
# print("c_tensors: ", c_tensors)
# print("d_tensors: ", d_tensors)

# b_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}/formatted/tensor_B*")
# c_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}/formatted/tensor_C*")

b_vec_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}/{app_name}/{test}/formatted/tensor_b*")
c_vec_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}/{app_name}/{test}/formatted/tensor_c*")
d_vec_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}/{app_name}/{test}/formatted/tensor_d*")

d_loc_paired = []

if not os.path.exists("SPARSE_TESTS/MAT_TMP_DIR"):
    os.makedirs("SPARSE_TESTS/MAT_TMP_DIR",exist_ok=True)

exit_status = os.system(f"rm -rf SPARSE_TESTS/{app_name}*")

if os.WEXITSTATUS(exit_status) != 0:
    raise RuntimeError(f"Command 'rm -rf SPARSE_TESTS/{app_name}*' returned non-zero exit status {os.WEXITSTATUS(exit_status)}.")

exit_status = os.system(f"rm -rf SPARSE_TESTS/MAT_TMP_DIR/tile*")

if os.WEXITSTATUS(exit_status) != 0:
    raise RuntimeError(f"Command 'rm -rf SPARSE_TESTS/{app_name}*' returned non-zero exit status {os.WEXITSTATUS(exit_status)}.")

tile = 0

os.chdir("SPARSE_TESTS")

if app_name == "tensor3_ttv":
    for b in b_tensors:
        for c in c_vec_tensors:
            tile_str = "tile" + str(tile)
            # b_loc = b[-7:]
            # c_loc = c[-3:]
            # print("b is:", b)
            b_loc = b.split("_")
            c_loc = c.split("_")

            index = b_loc.index("tile")
            b_loc = b_loc[index+1:]

            index = c_loc.index("tile")
            c_loc = c_loc[index+1:]

            # b_loc = b_loc.split("_")
            # c_loc = c_loc.split("_")

            # if(b_loc[1] == c_loc[0] and b_loc[3] == c_loc[1] and b_loc[0] == d_loc[0] and b_loc[2] == d_loc[1]):
            if(b_loc[2] == c_loc[0] and b_loc[5] == c_loc[1]):
                print(b,c)
                if not os.path.exists(f"./MAT_TMP_DIR/{tile_str}"):
                    os.mkdir(f"./MAT_TMP_DIR/{tile_str}")
                    
                shutil.copy(f"{b}/tensor_B_mode_0_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                shutil.copy(f"{b}/tensor_B_mode_0_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

                shutil.copy(f"{b}/tensor_B_mode_1_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                shutil.copy(f"{b}/tensor_B_mode_1_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

                shutil.copy(f"{b}/tensor_B_mode_2_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_2_crd")
                shutil.copy(f"{b}/tensor_B_mode_2_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_2_seg")

                shutil.copy(f"{b}/tensor_B_mode_vals", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

                shutil.copy(f"{b}/tensor_B_mode_shape", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

                # shutil.copy(f"{c}/c1_crd.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_c_mode_1_crd")
                # shutil.copy(f"{c}/c1_seg.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_c_mode_1_seg")

                shutil.copy(f"{c}/tensor_B_mode_0_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_c_mode_0_crd")
                shutil.copy(f"{c}/tensor_B_mode_0_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_c_mode_0_seg")

                shutil.copy(f"{c}/tensor_B_mode_vals", f"./MAT_TMP_DIR/{tile_str}/tensor_c_mode_vals")
                shutil.copy(f"{c}/tensor_B_mode_shape", f"./MAT_TMP_DIR/{tile_str}/tensor_c_mode_shape")

                tile = tile + 1

elif app_name == "tensor3_elemadd" or app_name == "tensor3_innerprod":
    for b in b_tensors:
        for c in c_tensors:
            tile_str = "tile" + str(tile)
            # b_loc = b[-7:]
            # c_loc = c[-3:]
            # print("b is:", b)
            b_loc = b.split("_")
            c_loc = c.split("_")

            index = b_loc.index("tile")
            b_loc = b_loc[index+1:]

            index = c_loc.index("tile")
            c_loc = c_loc[index+1:]

            # b_loc = b_loc.split("_")
            # c_loc = c_loc.split("_")

            # if(b_loc[1] == c_loc[0] and b_loc[3] == c_loc[1] and b_loc[0] == d_loc[0] and b_loc[2] == d_loc[1]):
            # if(b_loc[3] == c_loc[3] and b_loc[4] == c_loc[4] and b_loc[5] == c_loc[5] and b_loc[6] == c_loc[6] and b_loc[7] == c_loc[7] and b_loc[8] == c_loc[8]):
            if(b_loc == c_loc):
                print(b,c)
                if not os.path.exists(f"./MAT_TMP_DIR/{tile_str}"):
                    os.mkdir(f"./MAT_TMP_DIR/{tile_str}")
                    
                shutil.copy(f"{b}/tensor_B_mode_0_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                shutil.copy(f"{b}/tensor_B_mode_0_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

                shutil.copy(f"{b}/tensor_B_mode_1_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                shutil.copy(f"{b}/tensor_B_mode_1_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

                shutil.copy(f"{b}/tensor_B_mode_2_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_2_crd")
                shutil.copy(f"{b}/tensor_B_mode_2_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_2_seg")

                shutil.copy(f"{b}/tensor_B_mode_vals", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

                shutil.copy(f"{b}/tensor_B_mode_shape", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

                # shutil.copy(f"{c}/c1_crd.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_c_mode_1_crd")
                # shutil.copy(f"{c}/c1_seg.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_c_mode_1_seg")

                shutil.copy(f"{c}/tensor_B_mode_0_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                shutil.copy(f"{c}/tensor_B_mode_0_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                shutil.copy(f"{c}/tensor_B_mode_1_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                shutil.copy(f"{c}/tensor_B_mode_1_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                shutil.copy(f"{c}/tensor_B_mode_2_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_2_crd")
                shutil.copy(f"{c}/tensor_B_mode_2_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_2_seg")

                shutil.copy(f"{c}/tensor_B_mode_vals", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")
                shutil.copy(f"{c}/tensor_B_mode_shape", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                tile = tile + 1

elif app_name == "tensor3_ttm":
    for b in b_tensors:
        for c in c_tensors:
            tile_str = "tile" + str(tile)
            # b_loc = b[-7:]
            # c_loc = c[-3:]
            # print("b is:", b)
            split_list_b = b.split("/")
            split_list_c = c.split("/")
            # print("b list is", split_list)
            # print("b last is", split_list[6])
            b_loc_test = (split_list_b[7]).split("_")
            c_loc_test = (split_list_c[7]).split("_")
            # print("b_loc_test",b_loc_test[5])
            b_loc = (split_list_b[7]).split("_")
            c_loc = (split_list_c[7]).split("_")

            # b_loc = b_loc.split("_")
            # c_loc = c_loc.split("_")

            # print("b_loc is ",b_loc)
            # print("c_loc is ",c_loc)

            # if(b_loc[1] == c_loc[0] and b_loc[3] == c_loc[1] and b_loc[0] == d_loc[0] and b_loc[2] == d_loc[1]):
            if(b_loc[5] == c_loc[4] and b_loc[8] == c_loc[6]):
                # print(b,c)
                if not os.path.exists(f"./MAT_TMP_DIR/{tile_str}"):
                    os.mkdir(f"./MAT_TMP_DIR/{tile_str}")
                    
                shutil.copy(f"{b}/tensor_B_mode_0_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                shutil.copy(f"{b}/tensor_B_mode_0_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

                shutil.copy(f"{b}/tensor_B_mode_1_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                shutil.copy(f"{b}/tensor_B_mode_1_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

                shutil.copy(f"{b}/tensor_B_mode_2_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_2_crd")
                shutil.copy(f"{b}/tensor_B_mode_2_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_2_seg")

                shutil.copy(f"{b}/tensor_B_mode_vals", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

                shutil.copy(f"{b}/tensor_B_mode_shape", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

                # shutil.copy(f"{c}/c1_crd.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_c_mode_1_crd")
                # shutil.copy(f"{c}/c1_seg.txt", f"./MAT_TMP_DIR/{tile_str}/tensor_c_mode_1_seg")

                shutil.copy(f"{c}/tensor_B_mode_0_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                shutil.copy(f"{c}/tensor_B_mode_0_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                shutil.copy(f"{c}/tensor_B_mode_1_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                shutil.copy(f"{c}/tensor_B_mode_1_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                shutil.copy(f"{c}/tensor_B_mode_vals", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")
                shutil.copy(f"{c}/tensor_B_mode_shape", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                tile = tile + 1

elif app_name == "tensor3_mttkrp":
    for b in b_tensors:
        for c in c_tensors:
            for d in d_tensors:
                tile_str = "tile" + str(tile)
                
                b_loc = b.split("_")
                c_loc = c.split("_")
                d_loc = d.split("_")

                index = b_loc.index("tile")
                b_loc = b_loc[index+1:]

                index = c_loc.index("tile")
                c_loc = c_loc[index+1:]

                index = d_loc.index("tile")
                d_loc = d_loc[index+1:]

                if (c_loc[0] == d_loc[0] and c_loc[2] == d_loc[2] and b_loc[1] == c_loc[1] and b_loc[4] == c_loc[3] and b_loc[2] == d_loc[1] and b_loc[5] == d_loc[3]):
                    print(b,c,d)
                    if not os.path.exists(f"./MAT_TMP_DIR/{tile_str}"):
                        os.mkdir(f"./MAT_TMP_DIR/{tile_str}")
                        
                    shutil.copy(f"{b}/tensor_B_mode_0_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                    shutil.copy(f"{b}/tensor_B_mode_0_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

                    shutil.copy(f"{b}/tensor_B_mode_1_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                    shutil.copy(f"{b}/tensor_B_mode_1_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

                    shutil.copy(f"{b}/tensor_B_mode_2_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_2_crd")
                    shutil.copy(f"{b}/tensor_B_mode_2_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_2_seg")

                    shutil.copy(f"{b}/tensor_B_mode_vals", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

                    shutil.copy(f"{b}/tensor_B_mode_shape", f"./MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

                    shutil.copy(f"{c}/tensor_B_mode_0_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                    shutil.copy(f"{c}/tensor_B_mode_0_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                    shutil.copy(f"{c}/tensor_B_mode_1_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                    shutil.copy(f"{c}/tensor_B_mode_1_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                    shutil.copy(f"{c}/tensor_B_mode_vals", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")
                    shutil.copy(f"{c}/tensor_B_mode_shape", f"./MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                    shutil.copy(f"{d}/tensor_B_mode_0_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_crd")
                    shutil.copy(f"{d}/tensor_B_mode_0_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_seg")

                    shutil.copy(f"{d}/tensor_B_mode_1_crd", f"./MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_crd")
                    shutil.copy(f"{d}/tensor_B_mode_1_seg", f"./MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_seg")

                    shutil.copy(f"{d}/tensor_B_mode_vals", f"./MAT_TMP_DIR/{tile_str}/tensor_D_mode_vals")
                    shutil.copy(f"{d}/tensor_B_mode_shape", f"./MAT_TMP_DIR/{tile_str}/tensor_D_mode_shape")


                    tile = tile + 1

print("There are ", tile, " tiles")
