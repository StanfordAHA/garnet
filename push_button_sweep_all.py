import subprocess
import glob
import os

# app_list = ["matmul_ijk"]
app_list = ["mat_elemadd",
            "mat_elemmul",
            "mat_identity",
            "matmul_ijk"]

data = [
    'b1_ss',
    'cage3',
    'cage4',
    'cage5',
    'ch3-3-b1',
    'ch3-3-b2',
    'ch4-4-b1',
    'ch5-5-b1',
    'ch7-6-b1',
    'ex5',
    'farm',
    'football',
    'GD01_c',
    'GL7d10',
    'Hamrle1',
    'IG5-6',
    'kleemin',
    'klein-b1',
    'klein-b2',
    'LF10',
    'LFAT5',
    'lpi_bgprtr',
    'lpi_itest2',
    'lpi_itest6',
    'Maragal_1',
    'mk9-b1',
    'n2c6-b1',
    'n3c4-b1',
    'n3c4-b2',
    'n3c4-b3',
    'n3c4-b4',
    'n3c5-b1',
    'n3c6-b1',
    'n4c5-b1',
    'n4c6-b1',
    'pores_1',
    'Ragusa16',
    'Ragusa18',
    'rel3',
    'rel4',
    'rel5',
    'relat3',
    'relat4',
    'relat5',
    'Trec4',
    'Trec5',
    'Trec6',
    'Trec7',
    'Trefethen_20',
    'Trefethen_20b'
]

def replace_line(file_name, line_num, text):
    lines = open(file_name, 'r').readlines()
    lines[line_num - 1] = text + '\n' # 1-index
    out = open(file_name, 'w')
    out.writelines(lines)
    out.close()

for app in app_list:
    # modify and run load_cpu_sim
    load_path = "load_cpu_sim_tensors.py"
    replace_line(load_path, 5, f"app_name = '{app}'")

    # if app == "mat_vecmul":
    #     app = "mat_vecmul_ij"

    with open(f"sparse_sweep_results_1_{app}.txt", "w") as f:
        pass

    data_s = ""
    for d in data:
        data_s += f"'{d}',"
    replace_line(load_path, 9, f"datasets = [{data_s}]")

    command1 = f"rm -rf SPARSE_TESTS/"
    subprocess.run(command1, shell=True)
    command1 = f"mkdir SPARSE_TESTS/"
    subprocess.run(command1, shell=True)
    command1 = f"mkdir SPARSE_TESTS/MAT_TMP_DIR"
    subprocess.run(command1, shell=True)
    command1 = f"python3 load_cpu_sim_tensors.py"
    subprocess.run(command1, shell=True)

    print("Running ", app, "on data: ", data)

    #change regression (assume you have changed size and removed dense apps)
    regress_path = "/aha/aha/util/regress.py"
    replace_line(regress_path, 167, f"'{app}'")
    run_regress_fast = "aha regress fast"
    print("Running ", run_regress_fast)
    os.system(run_regress_fast)

    # if you want to load ALL datum from SUITESPARSE:
    # data_file = open("../sam/scripts/tensor_names/suitesparse_valid_small50.txt")
    # data_file_lines = data_file.readlines()
    # for line in data_file_lines:
    # data.append(line[:-1])

    print(data)

    for datum in data:
        print("TESTING ", datum)
        print(app, datum)
        f = open(f"sparse_sweep.txt", "w")
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
        
        print(datum)
        # with open(f"sparse_sweep_data_{app}_{datum}.txt", "w") as f:
        with open(f"sparse_sweep_results_1_{app}.txt", "a") as f:
            for line in lines:
                if "total time" in line:
                    time = line.split()[3]
                    print(datum, time)
                    f.write("data: \t" + str(datum) + "\t time: " + str(time) + "\n")
