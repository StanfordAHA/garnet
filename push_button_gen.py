import os

app_name = "matmul_ijk"
real_app_name = "matmul_ijk_crddrop"

tensor_datasets = [
    # 'rand_large_tensor1',
    # 'rand_large_tensor2',
    # 'rand_large_tensor3',
    # 'rand_large_tensor4',
    # 'rand_large_tensor5',
    # 'rand_large_tensor6',
    # 'rand_large_tensor7',
    # 'rand_large_tensor8',
    # 'rand_large_tensor9',
    # 'rand_large_tensor10'

    "rand_large_sp98_1",
    "rand_large_sp98_2",
    "rand_large_sp98_3",
    "rand_large_sp98_4",
    "rand_large_sp98_5",
    "rand_large_sp98_6",
    "rand_large_sp98_7",
    "rand_large_sp98_8",
    "rand_large_sp98_9",
    "rand_large_sp98_10"
            ]

matrix_datasets = [
#    'bcsstm26',
#     'G30',
#     'watt_2',
#     'G42',
#     'adder_trans_02',
#     'qiulp',
#     'west2021',
#     'adder_dcop_30',
#     'tols2000',
#     'rajat12'

    # "matrix_sp80_sm_1",
    # "matrix_sp80_sm_2",
    # "matrix_sp80_sm_3",
    # "matrix_sp80_sm_4",
    # "matrix_sp80_sm_5",
    # "matrix_sp80_sm_6",
    # "matrix_sp80_sm_7",
    # "matrix_sp80_sm_8",
    # "matrix_sp80_sm_9",
    # "matrix_sp80_sm_10"

    "matrix_sp65_sm_1",
    "matrix_sp65_sm_2",
    "matrix_sp65_sm_3",
    "matrix_sp65_sm_4",
    "matrix_sp65_sm_5",
    "matrix_sp65_sm_6",
    "matrix_sp65_sm_7",
    "matrix_sp65_sm_8",
    "matrix_sp65_sm_9",
    "matrix_sp65_sm_10"

]


datasets = []
if "tensor" in app_name:
    datasets = tensor_datasets
else:
    datasets = matrix_datasets

for datum in datasets:
    print("\n\n\n\n ", datum)
    #first copy formatted
    if "tensor" in app_name:
        copy_formatted = f"python3 copy_formatted_tensor_tiling.py {app_name} {datum}"
        print(copy_formatted)
        os.system(copy_formatted)
    else:
        copy_formatted = f"python3 copy_formatted.py {app_name} {datum}"
        print(copy_formatted)
        os.system(copy_formatted)

    #aha regress fast
    aha_regress_fast = f"aha regress fast"
    print(aha_regress_fast)
    os.system(aha_regress_fast)

    #generate script
    generate_script = f"python3 generate_sweep.py {real_app_name} {datum}"
    print(generate_script)
    os.system(generate_script)