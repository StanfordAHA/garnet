import numpy as np
import subprocess
import re

# aha test ../../../garnet/SPARSE_TESTS/{app}_{datum}/GLB_DIR/{app}_combined_seed_{datum} 
# --sparse --sparse-test-name {app} --sparse-comparison 
# /aha/garnet/SPARSE_TESTS/{app}_{datum}/GLB_DIR/{app}_combined_seed_{datum}/

'''
datasets = [
    "Trec4",
    "rel3",
    "relat3",
    "cage3",
    "Trec5",
    "n3c4-b1",
    "b1_ss",
    "GL7d10",
    "cage4",
    "ch3-3-b1",
    "rel4",
    "klein-b1",
    "n3c5-b1",
    "relat4",
    "lpi_itest2",
    "Trec6",
    "LFAT5",
    "Maragal_1",
    "n3c4-b4",
    "n3c4-b2",
    "n3c6-b1",
    "n2c6-b1",
    "n4c5-b1",
    "kleemin",
    "ch4-4-b1",
    "farm",
    "lpi_itest6",
    "ch3-3-b2",
    "LF10",
    "Ragusa18",
    "Trefethen_20b",
    "n3c4-b3",
    "Ragusa16",
    "Trefethen_20",
    "football",
    "ch5-5-b1",
    "ex5",
    "klein-b2",
    "pores_1",
    "GD01_c",
    "Hamrle1",
    "rel5",
    "relat5",
    "Trec7",
    "mk9-b1",
    "cage5",
    "lpi_bgprtr",
    "ch7-6-b1",
    "IG5-6",
    "n4c6-b1"
]
'''

datasets = [
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
    #'rel3',
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


# with open("person.txt", "w") as fp:
    # json.dump(person, fp)

# datasets = ["rel3"]

data_dict = {}

for key in datasets:
    data_dict[key] = None

# app_name = "matmul_ijk"
app_name = "mat_identity"

for datum_name in datasets:
    command = "aha glb ../../../garnet/SPARSE_TESTS/{app}_{datum}/GLB_DIR/{app}_combined_seed_{datum} --sparse --sparse-test-name {app} --sparse-comparison /aha/garnet/SPARSE_TESTS/{app}_{datum}/GLB_DIR/{app}_combined_seed_{datum}/ > temp_output.txt".format(app=app_name,datum=datum_name)
    
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

with open("mat_elemadd3_data.txt", 'w') as f: 
    for key, value in data_dict.items(): 
        f.write('%s:%s\n' % (key, value))