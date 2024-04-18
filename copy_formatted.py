import shutil
import glob
import os
import json
import sys

## copy_formatted, take 


# test = "bcsstm26" 
# test = "qiulp"
# test = "bcsstm26"
# test = "adder_dcop_30"
# test = "n4c6-b1"
# app_name = "mat_residual"
# app_name = "matmul_ijk"
# app_name = "matmul_ijk"
# app_name = "mat_mattransmul"
# app_name = "mat_vecmul_ij"
# app_name = "mat_elemadd"
app_name = sys.argv[1]
test = sys.argv[2]
# app_name = "mat_vecmul_ij"
# app_name = "mat_elemadd3"
# app_name = "mat_elemmul"
const_val = 2 # only for mat_mattransmul
mode_ns = False


tiles_accumulation = {}

b_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}/{app_name}/formatted/tensor_B*")
c_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}/{app_name}/formatted/tensor_C*")
d_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}/{app_name}/formatted/tensor_D*")
e_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}/{app_name}/formatted/tensor_E*")

b_ns_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_B_mode_2*")
c_ns_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_C_mode_2*")

print("b_tensors: ", b_tensors)
print("c_tensors: ", c_tensors)
print("d_tensors: ", d_tensors)

# b_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}/formatted/tensor_B*")
# c_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}/formatted/tensor_C*")

b_vec_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}/{app_name}/formatted/tensor_b*")
c_vec_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}/{app_name}/formatted/tensor_c*")
d_vec_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}/{app_name}/formatted/tensor_d*")
f_vec_tensors = glob.glob(f"/aha/garnet/tiles_{app_name}_{test}/{app_name}/formatted/tensor_f*")

d_loc_paired = []
b_loc_paired = []

b_loc_seen = set()
c_loc_seen = set()
d_loc_seen = set()


exit_status = os.system(f"rm -rf /aha/garnet/SPARSE_TESTS/{app_name}*")
exit_status = os.system(f"rm -rf /aha/garnet/SPARSE_TESTS/{app_name}_crddrop*")

if os.WEXITSTATUS(exit_status) != 0:
    raise RuntimeError(f"Command 'rm -rf /aha/garnet/SPARSE_TESTS/{app_name}*' returned non-zero exit status {os.WEXITSTATUS(exit_status)}.")

exit_status = os.system(f"rm -rf /aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/tile*")

if os.WEXITSTATUS(exit_status) != 0:
    raise RuntimeError(f"Command 'rm -rf /aha/garnet/SPARSE_TESTS/{app_name}*' returned non-zero exit status {os.WEXITSTATUS(exit_status)}.")

tile = 0


def find_tensor(tensor_list, tile_id):
    for temp in tensor_list:
        temp_loc = temp.split("_")
        index = temp_loc.index("tile")
        temp_loc = temp_loc[index+1:]
        # breakpoint()
        if temp_loc == tile_id:
            return temp
    return None

#os.chdir("SPARSE_TESTS")

if "matmul_ijk" in app_name and mode_ns == False:
    for b in b_tensors:
        for c in c_tensors:
            tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)
            # b_loc = b[-7:]
            # c_loc = c[-7:]
            b_loc = b.split("_")
            c_loc = c.split("_")

            index = b_loc.index("tile")
            b_loc = b_loc[index+1:]

            index = c_loc.index("tile")
            c_loc = c_loc[index+1:]

            if(b_loc[1] == c_loc[0] and b_loc[3] == c_loc[2]):
                print(b, c)

                if b_loc[2] not in tiles_accumulation:
                    tiles_accumulation[b_loc[2]] = []

                tiles_accumulation[b_loc[2]].append(tile_str)

                if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                    os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")
                
                shutil.copy(f"{b}/B0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                shutil.copy(f"{b}/B0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

                shutil.copy(f"{b}/B1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                shutil.copy(f"{b}/B1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

                shutil.copy(f"{b}/B_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

                shutil.copy(f"{b}/B_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

                shutil.copy(f"{c}/C0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                shutil.copy(f"{c}/C0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                shutil.copy(f"{c}/C1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                shutil.copy(f"{c}/C1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                shutil.copy(f"{c}/C_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

                shutil.copy(f"{c}/C_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                tile = tile + 1

if app_name == "matmul_ikj" and mode_ns == False:
    for b in b_tensors:
        for c in c_tensors:
            tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)
            # b_loc = b[-7:]
            # c_loc = c[-7:]
            b_loc = b.split("_")
            c_loc = c.split("_")

            index = b_loc.index("tile")
            b_loc = b_loc[index+1:]

            index = c_loc.index("tile")
            c_loc = c_loc[index+1:]

            if(b_loc[1] == c_loc[0] and b_loc[3] == c_loc[2]):
                print(b, c)

                if b_loc[2] not in tiles_accumulation:
                    tiles_accumulation[b_loc[2]] = []

                tiles_accumulation[b_loc[2]].append(tile_str)

                if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                    os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")
                
                shutil.copy(f"{b}/B0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                shutil.copy(f"{b}/B0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

                shutil.copy(f"{b}/B1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                shutil.copy(f"{b}/B1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

                shutil.copy(f"{b}/B_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

                shutil.copy(f"{b}/B_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

                shutil.copy(f"{c}/C0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                shutil.copy(f"{c}/C0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                shutil.copy(f"{c}/C1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                shutil.copy(f"{c}/C1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                shutil.copy(f"{c}/C_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

                shutil.copy(f"{c}/C_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                tile = tile + 1


if "matmul_ijk" in app_name and mode_ns == True:
    for b in b_ns_tensors:
        for c in c_ns_tensors:
            # mode 2 == mode 0, mode 3 == mode 1

            if "seg" in b or "seg" in c:
                continue

            tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)
            b_loc = b.split("_")
            c_loc = c.split("_")
            
            b_loc = b_loc[-2:]
            c_loc = c_loc[-2:]

            # breakpoint()

            if(b_loc[1] == c_loc[1]):
                tiles_accumulation[tile] = [b_loc, c_loc]
                if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                    os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")

                #only crds, copy mode 0
                shutil.copy(f"{b}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                shutil.copy(f"{c}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")

                b_seg_id = f"seg_{b_loc[0]}_{b_loc[1]}"
                c_seg_id = f"seg_{c_loc[0]}_{c_loc[1]}"

                b_seg_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_B_mode_2_{b_seg_id}"
                c_seg_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_C_mode_2_{c_seg_id}"

                shutil.copy(f"{b_seg_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")
                shutil.copy(f"{c_seg_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                # mode 1
                b_crd_id = f"crd_{b_loc[0]}_{b_loc[1]}"
                c_crd_id = f"crd_{c_loc[0]}_{c_loc[1]}"

                b_crd_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_B_mode_3_{b_crd_id}"
                c_crd_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_C_mode_3_{c_crd_id}"

                shutil.copy(f"{b_crd_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                shutil.copy(f"{c_crd_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")

                b_seg_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_B_mode_3_{b_seg_id}"
                c_seg_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_C_mode_3_{c_seg_id}"

                shutil.copy(f"{b_seg_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")
                shutil.copy(f"{c_seg_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                #vals
                b_vals_id = f"vals_{b_loc[0]}_{b_loc[1]}"
                c_vals_id = f"vals_{c_loc[0]}_{c_loc[1]}"

                b_vals_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_B_{b_vals_id}"
                c_vals_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_C_{c_vals_id}"

                shutil.copy(f"{b_vals_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")
                shutil.copy(f"{c_vals_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

                #shape
                with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape", "w") as f:
                    f.write("120\n30\n")
                with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape", "w") as f:
                    f.write("30\n120\n")

                tile = tile + 1

if app_name == "matmul_ikj" and mode_ns == True:
    for b in b_ns_tensors:
        for c in c_ns_tensors:
            # mode 2 == mode 0, mode 3 == mode 1

            if "seg" in b or "seg" in c:
                continue

            tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)
            b_loc = b.split("_")
            c_loc = c.split("_")
            
            b_loc = b_loc[-2:]
            c_loc = c_loc[-2:]

            # breakpoint()

            if(b_loc[1] == c_loc[1]):
                tiles_accumulation[tile] = [b_loc, c_loc]
                if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                    os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")

                #only crds, copy mode 0
                shutil.copy(f"{b}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                shutil.copy(f"{c}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")

                b_seg_id = f"seg_{b_loc[0]}_{b_loc[1]}"
                c_seg_id = f"seg_{c_loc[0]}_{c_loc[1]}"

                b_seg_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_B_mode_2_{b_seg_id}"
                c_seg_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_C_mode_2_{c_seg_id}"

                shutil.copy(f"{b_seg_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")
                shutil.copy(f"{c_seg_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                # mode 1
                b_crd_id = f"crd_{b_loc[0]}_{b_loc[1]}"
                c_crd_id = f"crd_{c_loc[0]}_{c_loc[1]}"

                b_crd_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_B_mode_3_{b_crd_id}"
                c_crd_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_C_mode_3_{c_crd_id}"

                shutil.copy(f"{b_crd_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                shutil.copy(f"{c_crd_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")

                b_seg_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_B_mode_3_{b_seg_id}"
                c_seg_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_C_mode_3_{c_seg_id}"

                shutil.copy(f"{b_seg_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")
                shutil.copy(f"{c_seg_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                #vals
                b_vals_id = f"vals_{b_loc[0]}_{b_loc[1]}"
                c_vals_id = f"vals_{c_loc[0]}_{c_loc[1]}"

                b_vals_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_B_{b_vals_id}"
                c_vals_file = f"/aha/garnet/tiles_{app_name}_{test}_ns/tensor_C_{c_vals_id}"

                shutil.copy(f"{b_vals_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")
                shutil.copy(f"{c_vals_file}", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

                #shape
                with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape", "w") as f:
                    f.write("120\n30\n")
                with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape", "w") as f:
                    f.write("30\n120\n")

                tile = tile + 1

elif app_name == "mat_elemadd" or app_name == "mat_elemmul":
    for b in b_tensors:
        for c in c_tensors:
            tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)
            # b_loc = b[-7:]
            # c_loc = c[-7:]
            # b_loc = b_loc.split("_")
            # c_loc = c_loc.split("_")
            b_loc = b.split("_")
            c_loc = c.split("_")

            index = b_loc.index("tile")
            b_loc = b_loc[index+1:]

            index = c_loc.index("tile")
            c_loc = c_loc[index+1:]

            if(b_loc == c_loc):
                print(b, c)
                if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                    os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")
                shutil.copy(f"{b}/B0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                shutil.copy(f"{b}/B0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

                shutil.copy(f"{b}/B1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                shutil.copy(f"{b}/B1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

                shutil.copy(f"{b}/B_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

                shutil.copy(f"{b}/B_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

                shutil.copy(f"{c}/C0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                shutil.copy(f"{c}/C0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                shutil.copy(f"{c}/C1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                shutil.copy(f"{c}/C1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                shutil.copy(f"{c}/C_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

                shutil.copy(f"{c}/C_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                # subprocess.call(["aha",
                #     "regress",
                #     "fast"],
                #     text=True)

                # shutil.copy("/aha/garnet//aha/garnet/SPARSE_TESTS/GLB_DIR/matmul_ijk_combined_seed_tile1/output_gold.npy", "/aha/garnet//aha/garnet/SPARSE_TESTS/GLB_DIR/matmul_ijk_combined_seed_tile1/bin")
                # shutil.copytree("/aha/garnet//aha/garnet/SPARSE_TESTS/GLB_DIR/matmul_ijk_combined_seed_tile1/bin", f"/aha/garnet//aha/garnet/SPARSE_TESTS/{tile_str}")
                tile = tile + 1
                # print("we are on tile ", tile)
elif app_name == "mat_mattransmul":
    for b in b_tensors:
        for c in c_vec_tensors:
            for d in d_vec_tensors:
                tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)
                b_loc = b[-7:]
                c_loc = c[-3:]
                d_loc = d[-3:]

                b_loc = b_loc.split("_")
                c_loc = c_loc.split("_")
                d_loc = d_loc.split("_")

                if(b_loc[1] == c_loc[0] and b_loc[3] == c_loc[1] and b_loc[0] == d_loc[0] and b_loc[2] == d_loc[1]):
                # if(b_loc[1] == d_loc[0] and b_loc[3] == d_loc[1] and b_loc[0] == c_loc[0] and b_loc[2] == c_loc[1]):
                    d_loc_paired.append(d_loc)

                    print(f"\n ----- TILE {tile} ----- \n")
                    print("B is: ", b) #in build_tb, B == C, c == d, d == f. (#FIXME: change build_tb)
                    print("C is: ", c)
                    print("d is: ", d)
                    print(f"\n ----- TILE {tile} ----- \n")
                    if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                        os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")
                        
                    shutil.copy(f"{b}/B0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                    shutil.copy(f"{b}/B0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                    shutil.copy(f"{b}/B1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                    shutil.copy(f"{b}/B1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                    shutil.copy(f"{b}/B_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

                    shutil.copy(f"{b}/B_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                    shutil.copy(f"{c}/c1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_1_crd")
                    shutil.copy(f"{c}/c1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_1_seg")

                    shutil.copy(f"{c}/c0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_0_crd")
                    shutil.copy(f"{c}/c0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_0_seg")

                    shutil.copy(f"{d}/d1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_1_crd")
                    shutil.copy(f"{d}/d1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_1_seg")

                    shutil.copy(f"{d}/d0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_0_crd")
                    shutil.copy(f"{d}/d0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_0_seg")

                    shutil.copy(f"{c}/c_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_vals")
                    shutil.copy(f"{c}/c_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_shape")

                    shutil.copy(f"{d}/d_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_vals")
                    shutil.copy(f"{d}/d_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_shape")

                    with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_vals", 'w') as file:
                        file.write(str(const_val))
                    
                    with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_e_mode_vals", 'w') as file:
                        file.write(str(const_val))
                    
                    tile = tile + 1
                elif d_loc not in d_loc_paired:
                    # case: B and c tiles are zero but d is nonzero. We have all d tiles. Just take a B and c tile, copy it and make it zero.'
                    d_loc_paired.append(d_loc)
                    print(f"\n ----- TILE D-unpaired {tile} ----- \n")
                    print("B (zero tile) is: ", b) #in build_tb, B == C, c == d, d == f. (#FIXME: change build_tb)
                    print("C (zero tile) is: ", c)
                    print("d is: ", d)
                    print(f"\n ----- TILE D-unpaired {tile} ----- \n")

                    if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                        os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")
                        
                    shutil.copy(f"{b}/B0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                    shutil.copy(f"{b}/B0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                    shutil.copy(f"{b}/B1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                    shutil.copy(f"{b}/B1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                    shutil.copy(f"{b}/B_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

                    # clear out C vals
                    with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals", 'r+') as file:
                        contents = file.read()
                        contents = contents.replace(contents, str(0))
                        file.seek(0)
                        file.write(contents)

                    shutil.copy(f"{b}/B_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                    shutil.copy(f"{c}/c1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_1_crd")
                    shutil.copy(f"{c}/c1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_1_seg")

                    shutil.copy(f"{c}/c0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_0_crd")
                    shutil.copy(f"{c}/c0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_0_seg")

                    shutil.copy(f"{d}/d1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_1_crd")
                    shutil.copy(f"{d}/d1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_1_seg")

                    shutil.copy(f"{d}/d0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_0_crd")
                    shutil.copy(f"{d}/d0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_0_seg")

                    shutil.copy(f"{c}/c_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_vals")

                    # clear out d vals
                    with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_vals", 'r+') as file:
                        contents = file.read()
                        contents = contents.replace(contents, str(0))
                        file.seek(0)
                        file.write(contents)

                    shutil.copy(f"{c}/c_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_shape")

                    shutil.copy(f"{d}/d_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_vals")
                    shutil.copy(f"{d}/d_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_shape")

                    with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_vals", 'w') as file:
                        file.write(str(const_val))
                    
                    with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_e_mode_vals", 'w') as file:
                        file.write(str(const_val))

                    tile = tile + 1
    print("d_loc_paired: ", d_loc_paired)
elif app_name == "mat_vecmul_ij":
    for b in b_tensors:
        for c in c_vec_tensors:
            tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)
            # b_loc = b[-7:]
            # c_loc = c[-3:]

            # b_loc = b_loc.split("_")
            # c_loc = c_loc.split("_")

            b_loc = b.split("_")
            c_loc = c.split("_")

            index = b_loc.index("tile")
            b_loc = b_loc[index+1:]

            index = c_loc.index("tile")
            c_loc = c_loc[index+1:]

            # if(b_loc[1] == c_loc[0] and b_loc[3] == c_loc[1] and b_loc[0] == d_loc[0] and b_loc[2] == d_loc[1]):
            if(b_loc[1] == c_loc[0] and b_loc[3] == c_loc[1]):
                print(b,c)
                if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                    os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")
                    
                shutil.copy(f"{b}/B0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                shutil.copy(f"{b}/B0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

                shutil.copy(f"{b}/B1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                shutil.copy(f"{b}/B1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

                shutil.copy(f"{b}/B_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

                shutil.copy(f"{b}/B_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

                # shutil.copy(f"{c}/c1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_c_mode_1_crd")
                # shutil.copy(f"{c}/c1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_c_mode_1_seg")

                shutil.copy(f"{c}/c1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_c_mode_0_crd")
                shutil.copy(f"{c}/c1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_c_mode_0_seg")

                shutil.copy(f"{c}/c_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_c_mode_vals")
                shutil.copy(f"{c}/c_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_c_mode_shape")

                tile = tile + 1
elif app_name == "mat_residual":
    for b in b_vec_tensors:
        for c in c_tensors:
            for d in d_vec_tensors:
                tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)
                b_loc = b[-3:]
                c_loc = c[-7:]
                d_loc = d[-3:]

                b_loc = b_loc.split("_")
                c_loc = c_loc.split("_")
                d_loc = d_loc.split("_")

                # if(b_loc[1] == c_loc[0] and b_loc[3] == c_loc[1] and b_loc[0] == d_loc[0] and b_loc[2] == d_loc[1]):
                if(c_loc[0] == b_loc[0] and c_loc[2] == b_loc[1] and c_loc[1] == d_loc[0] and c_loc[3] == d_loc[1]):
                    print(b, c, d)
                    b_loc_paired.append(b_loc)
                    
                    if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                        os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")
                        
                    shutil.copy(f"{c}/C0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                    shutil.copy(f"{c}/C0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                    shutil.copy(f"{c}/C1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                    shutil.copy(f"{c}/C1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                    shutil.copy(f"{c}/C_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

                    shutil.copy(f"{c}/C_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                    shutil.copy(f"{b}/b1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_1_crd")
                    shutil.copy(f"{b}/b1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_1_seg")

                    shutil.copy(f"{b}/b0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_0_crd")
                    shutil.copy(f"{b}/b0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_0_seg")

                    shutil.copy(f"{d}/d1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_1_crd")
                    shutil.copy(f"{d}/d1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_1_seg")

                    shutil.copy(f"{d}/d0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_0_crd")
                    shutil.copy(f"{d}/d0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_0_seg")

                    shutil.copy(f"{b}/b_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_vals")
                    shutil.copy(f"{b}/b_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_shape")

                    shutil.copy(f"{d}/d_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_vals")
                    shutil.copy(f"{d}/d_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_shape")

                    tile = tile + 1
                elif b_loc not in b_loc_paired:
                    b_loc_paired.append(b_loc)
                    
                    if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                        os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")
                        
                    shutil.copy(f"{c}/C0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                    shutil.copy(f"{c}/C0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                    shutil.copy(f"{c}/C1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                    shutil.copy(f"{c}/C1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                    shutil.copy(f"{c}/C_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

                    # clear out C vals
                    with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals", 'r+') as file:
                        contents = file.read()
                        contents = contents.replace(contents, str(0))
                        file.seek(0)
                        file.write(contents)

                    shutil.copy(f"{c}/C_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                    shutil.copy(f"{b}/b1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_1_crd")
                    shutil.copy(f"{b}/b1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_1_seg")

                    shutil.copy(f"{b}/b0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_0_crd")
                    shutil.copy(f"{b}/b0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_0_seg")

                    shutil.copy(f"{d}/d1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_1_crd")
                    shutil.copy(f"{d}/d1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_1_seg")

                    shutil.copy(f"{d}/d0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_0_crd")
                    shutil.copy(f"{d}/d0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_0_seg")

                    shutil.copy(f"{b}/b_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_vals")
                    shutil.copy(f"{b}/b_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_b_mode_shape")

                    shutil.copy(f"{d}/d_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_vals")
                    shutil.copy(f"{d}/d_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_shape")

                    # clear out d vals
                    with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_d_mode_vals", 'r+') as file:
                        contents = file.read()
                        contents = contents.replace(contents, str(0))
                        file.seek(0)
                        file.write(contents)

                    tile = tile + 1
elif app_name == "mat_mask_tri":
    for b in b_tensors:
        for c in c_tensors:
            # b_loc = b[-7:]
            # c_loc = c[-7:]
            b_loc = b.split("_")
            c_loc = c.split("_")

            index = b_loc.index("tile")
            b_loc = b_loc[index+1:]

            index = c_loc.index("tile")
            c_loc = c_loc[index+1:]

            if not (b_loc[0] == c_loc[0] and b_loc[2] == c_loc[2]):
                continue

            for d in d_tensors:
                tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)
                d_loc = d.split("_")
                index = d_loc.index("tile")
                d_loc = d_loc[index+1:]

                if(c_loc[1] == d_loc[0] and c_loc[3] == d_loc[2] and b_loc[1] == d_loc[1] and b_loc[3] == d_loc[3] and b_loc[0] == c_loc[0] and b_loc[2] == c_loc[2]):
                    print(b, c, d)
                    if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                        os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")

                    shutil.copy(f"{b}/B0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                    shutil.copy(f"{b}/B0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

                    shutil.copy(f"{b}/B1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                    shutil.copy(f"{b}/B1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

                    shutil.copy(f"{b}/B_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

                    shutil.copy(f"{b}/B_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

                    shutil.copy(f"{c}/C0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                    shutil.copy(f"{c}/C0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                    shutil.copy(f"{c}/C1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                    shutil.copy(f"{c}/C1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                    shutil.copy(f"{c}/C_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

                    shutil.copy(f"{c}/C_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                    shutil.copy(f"{d}/D0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_crd")
                    shutil.copy(f"{d}/D0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_seg")

                    shutil.copy(f"{d}/D1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_crd")
                    shutil.copy(f"{d}/D1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_seg")

                    shutil.copy(f"{d}/D_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_vals")

                    shutil.copy(f"{d}/D_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_shape")

                    # subprocess.call(["aha",
                    #     "regress",
                    #     "fast"],
                    #     text=True)

                    # shutil.copy("/aha/garnet//aha/garnet/SPARSE_TESTS/GLB_DIR/matmul_ijk_combined_seed_tile1/output_gold.npy", "/aha/garnet//aha/garnet/SPARSE_TESTS/GLB_DIR/matmul_ijk_combined_seed_tile1/bin")
                    # shutil.copytree("/aha/garnet//aha/garnet/SPARSE_TESTS/GLB_DIR/matmul_ijk_combined_seed_tile1/bin", f"/aha/garnet//aha/garnet/SPARSE_TESTS/{tile_str}")
                    tile = tile + 1
elif app_name == "mat_vecmul_iter":
    for b in b_tensors:
        for c in c_tensors:
            # b_loc = b[-7:]
            # c_loc = c[-7:]
            b_loc = b.split("_")
            c_loc = c.split("_")

            index = b_loc.index("tile")
            b_loc = b_loc[index+1:]

            index = c_loc.index("tile")
            c_loc = c_loc[index+1:]

            # check j coord
            if not (b_loc[1] == c_loc[0] and b_loc[3] == c_loc[2]):
                continue

            for d in d_tensors:
                d_loc = d.split("_")
                index = d_loc.index("tile")
                d_loc = d_loc[index+1:]

                # check k coord
                if not (c_loc[1] == d_loc[0] and c_loc[3] == d_loc[2]):
                    continue

                for e in e_tensors:
                    e_loc = e.split("_")
                    index = e_loc.index("tile")
                    e_loc = e_loc[index+1:]

                    # check l coord
                    if not (d_loc[1] == e_loc[0] and d_loc[3] == e_loc[2]):
                        continue

                    for f in f_vec_tensors:
                        tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)
                        f_loc = f.split("_")
                        index = f_loc.index("tile")
                        f_loc = f_loc[index+1:]

                        # check m coord 
                        if (d_loc[1] == e_loc[0] and d_loc[3] == e_loc[2] and c_loc[1] == d_loc[0] and c_loc[3] == d_loc[2] and b_loc[1] == c_loc[0] and b_loc[3] == c_loc[2] and e_loc[1] == f_loc[0] and e_loc[3] == f_loc[1]):
                            print(b, c, d, e, f)
                            if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                                os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")

                            shutil.copy(f"{b}/B0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                            shutil.copy(f"{b}/B0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

                            shutil.copy(f"{b}/B1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                            shutil.copy(f"{b}/B1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

                            shutil.copy(f"{b}/B_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

                            shutil.copy(f"{b}/B_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

                            shutil.copy(f"{c}/C0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                            shutil.copy(f"{c}/C0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                            shutil.copy(f"{c}/C1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                            shutil.copy(f"{c}/C1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                            shutil.copy(f"{c}/C_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

                            shutil.copy(f"{c}/C_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                            shutil.copy(f"{d}/D0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_crd")
                            shutil.copy(f"{d}/D0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_seg")

                            shutil.copy(f"{d}/D1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_crd")
                            shutil.copy(f"{d}/D1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_seg")

                            shutil.copy(f"{d}/D_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_vals")

                            shutil.copy(f"{d}/D_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_shape")

                            shutil.copy(f"{e}/E0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_E_mode_0_crd")
                            shutil.copy(f"{e}/E0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_E_mode_0_seg")

                            shutil.copy(f"{e}/E1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_E_mode_1_crd")
                            shutil.copy(f"{e}/E1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_E_mode_1_seg")

                            shutil.copy(f"{e}/E_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_E_mode_vals")

                            shutil.copy(f"{e}/E_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_E_mode_shape")

                            shutil.copy(f"{f}/f1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_0_crd")
                            shutil.copy(f"{f}/f1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_0_seg")

                            shutil.copy(f"{f}/f_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_vals")
                            shutil.copy(f"{f}/f_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_f_mode_shape")
                            
                            tile = tile + 1
elif app_name == "mat_sddmm":
    for b in b_tensors:
        for c in c_tensors:
            for d in d_tensors:
                tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)

                b_loc = b[-7:]
                c_loc = c[-7:]
                d_loc = d[-7:]

                b_loc = b_loc.split("_")
                c_loc = c_loc.split("_")
                d_loc = d_loc.split("_")

                # first j, then i (k is a free coordinate)
                # if(b_loc[0] == d_loc[1] and b_loc[2] == d_loc[3] and b_loc[1] == c_loc[0] and b_loc[3] == c_loc[2]):
                #matmul rule for C and D, elemmul rule for B and CD
                if(c_loc[1] == d_loc[1] and c_loc[3] == d_loc[3] and b_loc[0] == c_loc[0] and b_loc[2] == c_loc[2] and b_loc[1] == d_loc[0] and b_loc[3] == d_loc[2]):
                    print(b, c, d)
                    if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                        os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")
                    
                    shutil.copy(f"{b}/B0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                    shutil.copy(f"{b}/B0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

                    shutil.copy(f"{b}/B1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                    shutil.copy(f"{b}/B1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

                    shutil.copy(f"{b}/B_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

                    shutil.copy(f"{b}/B_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

                    shutil.copy(f"{c}/C0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                    shutil.copy(f"{c}/C0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                    shutil.copy(f"{c}/C1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                    shutil.copy(f"{c}/C1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                    shutil.copy(f"{c}/C_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

                    shutil.copy(f"{c}/C_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                    shutil.copy(f"{d}/D0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_crd")
                    shutil.copy(f"{d}/D0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_seg")

                    shutil.copy(f"{d}/D1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_crd")
                    shutil.copy(f"{d}/D1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_seg")

                    shutil.copy(f"{d}/D_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_vals")

                    shutil.copy(f"{d}/D_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_shape")

                    tile = tile + 1

elif app_name == "mat_elemadd3":
    for b in b_tensors:
        for c in c_tensors:
            b_loc = b.split("_")
            c_loc = c.split("_")

            index = b_loc.index("tile")
            b_loc = b_loc[index+1:]

            index = c_loc.index("tile")
            c_loc = c_loc[index+1:]

            b_loc_seen.add(tuple(b_loc))
            c_loc_seen.add(tuple(c_loc))

            if (b_loc != c_loc):
                continue

            for d in d_tensors:
                tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)
                d_loc = d.split("_")


                index = d_loc.index("tile")
                d_loc = d_loc[index+1:]

                d_loc_seen.add(tuple(d_loc))
            
                if(b_loc == c_loc and b_loc == d_loc):
                    print(b, c, d)
                    if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
                        os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")
                    shutil.copy(f"{b}/B0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
                    shutil.copy(f"{b}/B0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

                    shutil.copy(f"{b}/B1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
                    shutil.copy(f"{b}/B1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

                    shutil.copy(f"{b}/B_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

                    shutil.copy(f"{b}/B_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

                    shutil.copy(f"{c}/C0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
                    shutil.copy(f"{c}/C0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

                    shutil.copy(f"{c}/C1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
                    shutil.copy(f"{c}/C1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

                    shutil.copy(f"{c}/C_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

                    shutil.copy(f"{c}/C_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

                    shutil.copy(f"{d}/D0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_crd")
                    shutil.copy(f"{d}/D0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_seg")

                    shutil.copy(f"{d}/D1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_crd")
                    shutil.copy(f"{d}/D1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_seg")

                    shutil.copy(f"{d}/D_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_vals")

                    shutil.copy(f"{d}/D_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_shape")

                    # subprocess.call(["aha",
                    #     "regress",
                    #     "fast"],
                    #     text=True)

                    # shutil.copy("/aha/garnet//aha/garnet/SPARSE_TESTS/GLB_DIR/matmul_ijk_combined_seed_tile1/output_gold.npy", "/aha/garnet//aha/garnet/SPARSE_TESTS/GLB_DIR/matmul_ijk_combined_seed_tile1/bin")
                    # shutil.copytree("/aha/garnet//aha/garnet/SPARSE_TESTS/GLB_DIR/matmul_ijk_combined_seed_tile1/bin", f"/aha/garnet//aha/garnet/SPARSE_TESTS/{tile_str}")
                    tile = tile + 1
                    # print("we are on tile ", tile)

print("tiles_accumulation: ", tiles_accumulation)

with open("../tiles_accumulation.json", "w") as file:
    json.dump(tiles_accumulation, file)

if app_name == "mat_elemadd3":
    shared_BC_not_D = (b_loc_seen & c_loc_seen) - d_loc_seen
    shared_BD_not_C = (b_loc_seen & d_loc_seen) - c_loc_seen
    shared_CD_not_B = (c_loc_seen & d_loc_seen) - b_loc_seen

    print("shared BC not D: ", shared_BC_not_D)
    print("shared BD not C: ", shared_BD_not_C)
    print("shared CD not B: ", shared_CD_not_B)

    for tile_id in shared_BD_not_C:
        b = find_tensor(b_tensors, list(tile_id))
        if b == None:
            raise Exception

        d = find_tensor(d_tensors, list(tile_id))
        if d == None:
            raise Exception
        
        # go to tile file in MAT_TMP_DIR. create empty D
        
        tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)

        if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
            os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")
        
        c = c_tensors[0]
        shutil.copy(f"{b}/B0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
        shutil.copy(f"{b}/B0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

        shutil.copy(f"{b}/B1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
        shutil.copy(f"{b}/B1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

        shutil.copy(f"{b}/B_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

        shutil.copy(f"{b}/B_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

        shutil.copy(f"{c}/C0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
        shutil.copy(f"{c}/C0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

        shutil.copy(f"{c}/C1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
        shutil.copy(f"{c}/C1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

        shutil.copy(f"{c}/C_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

        shutil.copy(f"{c}/C_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

        shutil.copy(f"{d}/D0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_crd")
        shutil.copy(f"{d}/D0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_seg")

        shutil.copy(f"{d}/D1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_crd")
        shutil.copy(f"{d}/D1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_seg")

        shutil.copy(f"{d}/D_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_vals")

        shutil.copy(f"{d}/D_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_shape")

        #write ones to vals
        lines = []
        with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals", 'r') as file:
            lines = file.readlines()
        with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals", 'w') as file:
            file.writelines(['0\n']*len(lines))
        
        tile = tile+1

    for tile_id in shared_CD_not_B:
        c = find_tensor(c_tensors, list(tile_id))
        if c == None:
            raise Exception

        d = find_tensor(d_tensors, list(tile_id))
        if d == None:
            raise Exception
        
        # go to tile file in MAT_TMP_DIR. create empty B
        
        tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)

        if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
            os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")

        b = b_tensors[0]
        
        shutil.copy(f"{b}/B0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
        shutil.copy(f"{b}/B0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

        shutil.copy(f"{b}/B1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
        shutil.copy(f"{b}/B1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

        shutil.copy(f"{b}/B_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

        shutil.copy(f"{b}/B_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

        shutil.copy(f"{c}/C0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
        shutil.copy(f"{c}/C0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

        shutil.copy(f"{c}/C1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
        shutil.copy(f"{c}/C1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

        shutil.copy(f"{c}/C_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

        shutil.copy(f"{c}/C_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

        shutil.copy(f"{d}/D0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_crd")
        shutil.copy(f"{d}/D0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_seg")

        shutil.copy(f"{d}/D1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_crd")
        shutil.copy(f"{d}/D1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_seg")

        shutil.copy(f"{d}/D_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_vals")

        shutil.copy(f"{d}/D_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_shape")


        #write ones to vals
        lines = []
        with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals", 'r') as file:
            lines = file.readlines()
        with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals", 'w') as file:
            file.writelines(['0\n']*len(lines))
        
        tile = tile+1

    for tile_id in shared_BD_not_C:
        b = find_tensor(b_tensors, list(tile_id))
        if b == None:
            raise Exception

        d = find_tensor(d_tensors, list(tile_id))
        if d == None:
            raise Exception
        
        # go to tile file in MAT_TMP_DIR. create empty B
        
        tile_str = str(app_name) + "-" + str(test) + "_tile" + str(tile)

        if not os.path.exists(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}"):
            os.mkdir(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}")

        c = c_tensors[0]
        
        shutil.copy(f"{b}/B0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_crd")
        shutil.copy(f"{b}/B0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_0_seg")

        shutil.copy(f"{b}/B1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_crd")
        shutil.copy(f"{b}/B1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_1_seg")

        shutil.copy(f"{b}/B_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_vals")

        shutil.copy(f"{b}/B_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_B_mode_shape")

        shutil.copy(f"{c}/C0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_crd")
        shutil.copy(f"{c}/C0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_0_seg")

        shutil.copy(f"{c}/C1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_crd")
        shutil.copy(f"{c}/C1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_1_seg")

        shutil.copy(f"{c}/C_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals")

        shutil.copy(f"{c}/C_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_shape")

        shutil.copy(f"{d}/D0_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_crd")
        shutil.copy(f"{d}/D0_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_0_seg")

        shutil.copy(f"{d}/D1_crd.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_crd")
        shutil.copy(f"{d}/D1_seg.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_1_seg")

        shutil.copy(f"{d}/D_vals.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_vals")

        shutil.copy(f"{d}/D_shape.txt", f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_D_mode_shape")


        #write ones to vals
        lines = []
        with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals", 'r') as file:
            lines = file.readlines()
        with open(f"/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR/{tile_str}/tensor_C_mode_vals", 'w') as file:
            file.writelines(['0\n']*len(lines))
        
        tile = tile+1


print("there are ", tile, " tiles")
