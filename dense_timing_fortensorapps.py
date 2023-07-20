import numpy as np
import subprocess
import re

#base aha test command:
# aha test ../../../garnet/SPARSE_TESTS/{app}_{datum}/GLB_DIR/{app}_combined_seed_{datum} 
# --sparse --sparse-test-name {app} --sparse-comparison 
# /aha/garnet/SPARSE_TESTS/{app}_{datum}/GLB_DIR/{app}_combined_seed_{datum}/

datasets = [
    'rand_tensor1',
    'rand_tensor2',
    'rand_tensor3',
    'rand_tensor4',
    'rand_tensor5',
    'rand_tensor6',
    'rand_tensor7',
    'rand_tensor8',
    'rand_tensor9',
    'rand_tensor10',
    'rand_tensor11',
    'rand_tensor12',
    'rand_tensor13',
    'rand_tensor14',
    'rand_tensor15',
    'rand_tensor16',
    'rand_tensor17',
    'rand_tensor18',
    'rand_tensor19',
    'rand_tensor20',
    'rand_tensor21',
    'rand_tensor22',
    'rand_tensor23',
    'rand_tensor24',
    'rand_tensor25',
    'rand_tensor26',
    'rand_tensor27',
    'rand_tensor28',
    'rand_tensor29',
    'rand_tensor30',
    'rand_tensor31',
    'rand_tensor32',
    'rand_tensor33',
    'rand_tensor34',
    'rand_tensor35',
    'rand_tensor36',
    'rand_tensor37',
    'rand_tensor38',
    'rand_tensor39',
    'rand_tensor40',
    'rand_tensor41',
    'rand_tensor42',
    'rand_tensor43',
    'rand_tensor44',
    'rand_tensor45',
    'rand_tensor46',
    'rand_tensor47',
    'rand_tensor48',
    'rand_tensor49',
    'rand_tensor50'
]

data_dict = {}

for key in datasets:
    data_dict[key] = None

# change this
app_name = "tensor3_elemadd"
# app_name = "tensor3_innerprod"
# app_name = "tensor3_ttv"
# app_name = "tensor3_ttm"
# app_name = "tensor3_mttkrp"

for datum_name in datasets:
    command = "aha test ../../../garnet/SPARSE_TESTS/{app}_{datum}/GLB_DIR/{app}_combined_seed_{datum} --sparse --sparse-test-name {app} --sparse-comparison /aha/garnet/SPARSE_TESTS/{app}_{datum}/GLB_DIR/{app}_combined_seed_{datum}/ > temp_output.txt".format(app=app_name,datum=datum_name)
    
    subprocess.run(command, shell=True)

    keyword = "total time"
    file_path = "temp_output.txt"

    with open(file_path, "r") as file:
        lines_with_keyword = [line for line in file if keyword in line]
    
    for line in lines_with_keyword:
        print(line)

        pattern = r"\d+\.\d+"

        number = re.search(pattern, line)

        if number:
            extracted_number = number.group()
            data_dict[datum_name] = float(extracted_number)

print(data_dict)

with open("{app_name}_data.txt", 'w') as f: 
    for key, value in data_dict.items(): 
        f.write('%s:%s\n' % (key, value))
