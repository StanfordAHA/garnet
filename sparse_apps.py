import subprocess
import glob
import random
import os

app = "mat_mattransmul"
test = "rel5" 
num_samples = 50

#data = ["cage3"]
#data = ["Trec4"]
#data = []
#data_file = open("../sam/scripts/tensor_names/suitesparse_valid_small50.txt")
#data_file_lines = data_file.readlines()
#for line in data_file_lines:
#    data.append(line[:-1])

name_list = glob.glob(f"./SPARSE_TESTS/{app}_tile*")
# print(name_list)

lst = [int(tile.replace(f"./SPARSE_TESTS/{app}_tile", "")) for tile in name_list]
# print(lst)
largest_num = max(lst)

#take random sample
# tiles_to_run = random.sample(range(0, largest_num),num_samples)

print("NUM TILES: ", largest_num)

name_list = []
for i in range(largest_num+1):
        name_list.append(f"tile{i}")
# for i in tiles_to_run:
#         name_list.append(f"tile{i}")

data = name_list

# print(data)

f = open(f"sparse_sweep_{app}_{test}.txt", "w")

for datum in data:
#     print(app, datum)
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

        path = f"/aha/garnet/tensor_X_matmul_tiled/{test}/{datum}"
        if not os.path.exists(path):
                os.makedirs(path)

        command_clear = f"rm /aha/garnet/tensor_X_matmul_tiled/{test}/{datum}/*"
        os.system(command_clear)
        
        command = f"cp /aha/garnet/tests/test_app/tensor_X* /aha/garnet/tensor_X_matmul_tiled/{test}/{datum}"
        print(command)
        os.system(command)

f.close()

name_list = glob.glob(f"./SPARSE_TESTS/{app}_tile*")
print(name_list)

lst = [int(tile.replace(f"./SPARSE_TESTS/{app}_tile", "")) for tile in name_list]
print(lst)
largest_num = max(lst)


name_list = []
for i in range(largest_num+1):
        name_list.append(f"tile{i}")

data = name_list
print(name_list)

f2 = open(f"sparse_sweep_{app}_{test}.txt", "r")

lines = f2.readlines()

total_time = 0
idx = 0
for line in lines:
   if "total time" in line:
       time = line.split()[3]
       print(data[idx], time)
       total_time += float(time)
       idx = idx + 1

print(f"total time for {app} {datum} is ", total_time)

print("the largest number is ", largest_num)
