import numpy as np
import subprocess

# change this
# app_name = "mat_elemadd3"
# app_name = "mat_elemmul"
app_name = "mat_vecmul"

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

for datum_name in datasets:
    command1 = f"mkdir SPARSE_TESTS/MAT_TMP_DIR/{datum_name}/"
    subprocess.run(command1, shell=True)
    command = f"cp SUITESPARSE_FORMATTED/{datum_name}/{app_name}/* SPARSE_TESTS/MAT_TMP_DIR/{datum_name}"
    subprocess.run(command, shell=True)
