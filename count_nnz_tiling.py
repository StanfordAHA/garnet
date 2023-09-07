import glob
def count_nonzeros(matrix_values_file):
    with open(matrix_values_file, 'r') as values_file:
        matrix_values = [float(val) for val in values_file.readlines()]

    nonzeros = sum(1 for val in matrix_values if val != 0)

    return nonzeros


tile_dirs = glob.glob("SPARSE_TESTS/MAT_TMP_DIR/tile*")
num_tiles = len(tile_dirs)
print("there are ", num_tiles, "tiles")
limit = 900

tot_num_nonzeros = 0
for tile_num in range(0,num_tiles):
    tensor_C_values_file = f'SPARSE_TESTS/MAT_TMP_DIR/tile{tile_num}/tensor_B_mode_vals'

    num_nonzeros = count_nonzeros(tensor_C_values_file)
    if num_nonzeros >= limit:
        print("error! too many nonzeros in tensorB, tile", tile_num)

#     tot_num_nonzeros += num_nonzeros

# average_num_nonzeros = tot_num_nonzeros / 9
# print("for matrix C, the average number of non-zero values is", average_num_nonzeros)

tot_num_nonzeros = 0

for tile_num in range(0,num_tiles):
    tensor_C_values_file = f'SPARSE_TESTS/MAT_TMP_DIR/tile{tile_num}/tensor_C_mode_vals'

    num_nonzeros = count_nonzeros(tensor_C_values_file)
    if num_nonzeros >= limit:
        print("error! too many nonzeros in tensorc, tile", tile_num)
#     tot_num_nonzeros += num_nonzeros

# average_num_nonzeros = tot_num_nonzeros / 6
# print("for matrix B, the average number of non-zero values is", average_num_nonzeros)
