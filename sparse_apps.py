import subprocess
import glob

app = "matmul_ijk"

#data = ["cage3"]
#data = ["Trec4"]
#data = []
#data_file = open("../sam/scripts/tensor_names/suitesparse_valid_small50.txt")
#data_file_lines = data_file.readlines()
#for line in data_file_lines:
#    data.append(line[:-1])

name_list = glob.glob("./SPARSE_TESTS/matmul_ijk_tile*")
print(name_list)

lst = [int(tile.replace("./SPARSE_TESTS/matmul_ijk_tile", "")) for tile in name_list]
print(lst)
largest_num = max(lst)

print(largest_num)

name_list = []
for i in range(largest_num+1):
        name_list.append(f"tile{i}")

data = name_list

print(data)

f = open("sparse_sweep.txt", "w")

for datum in data:
    print(app, datum)
    subprocess.call(["aha", 
                "glb", 
                f"../../../garnet/SPARSE_TESTS/{app}_{datum}/GLB_DIR/{app}_combined_seed_{datum}",  
                "--sparse", 
                "--sparse-test-name", 
                f"{app}", 
                "--sparse-comparison", 
                f"/aha/garnet/SPARSE_TESTS/{app}_{datum}/GLB_DIR/{app}_combined_seed_{datum}/"],
                text=True,
                stdout=f)

f.close()

#f2 = open("sparse_sweep.txt", "r")
#
#lines = f2.readlines()
#
#print(data)
#idx = 0
#for line in lines:
#    if "total time" in line:
#        time = line.split()[3]
#        print(data[idx], time)
#        idx = idx + 1
