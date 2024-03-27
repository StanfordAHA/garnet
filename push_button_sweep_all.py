import subprocess
import glob

app_list = []
data = ["cage3"]

def replace_line(file_name, line_num, text):
    lines = open(file_name, 'r').readlines()
    lines[line_num] = text
    out = open(file_name, 'w')
    out.writelines(lines)
    out.close()

for app in app_list:
    print("Running ", app, "on data: ", data)

    #change regression (assume you have changed size and removed dense apps)
    regress_path = "/aha/aha/util/regress.py"
    replace_line(regress_path, 167, f"'{app_name}'")
    run_regress_fast = "aha regress fast"
    print("Running ", run_regress_fast)
    os.system(run_regress_fast)

    # if you want to load ALL datum from SUITESPARSE:
    # data_file = open("../sam/scripts/tensor_names/suitesparse_valid_small50.txt")
    # data_file_lines = data_file.readlines()
    # for line in data_file_lines:
    # data.append(line[:-1])

    print(data)

    f = open(f"sparse_sweep.txt", "w")

    for datum in data:
        print("TESTING ", datum)
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

        f2 = open("sparse_sweep.txt", "r")
        
        lines = f2.readlines()
        
        print(data)
        idx = 0

        with open(f"sparse_sweep_data_{app}_{datum}.txt", "w") as f:
            for line in lines:
            if "total time" in line:
                time = line.split()[3]
                print(data[idx], time)
                f.write("data: \t" + data + "\t time: " + time + "\n")
                idx = idx + 1