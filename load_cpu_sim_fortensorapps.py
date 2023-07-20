import numpy as np
import subprocess

# change this
app_name = "tensor3_elemadd"
# app_name = "tensor3_innerprod"
# app_name = "tensor3_ttv"
# app_name = "tensor3_ttm"
# app_name = "tensor3_mttkrp"
tensor_format = "sss012"
# "tensor3_ttv"
# "tensor3_elemadd",
# "tensor3_elemmul",
# "tensor3_identity",
# "tensor3_innerprod",
# "tensor3_mttkrp",
# "tensor3_ttm",
# "tensor3_ttv",

datasets = [
    #'fb1k',
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

for datum_name in datasets:
    command1 = f"mkdir SPARSE_TESTS/MAT_TMP_DIR/{datum_name}/"
    subprocess.run(command1, shell=True)
    command = f"cp -r FROST_FORMATTED/{datum_name}/{app_name}/{tensor_format}/* SPARSE_TESTS/MAT_TMP_DIR/{datum_name}"
    subprocess.run(command, shell=True)
