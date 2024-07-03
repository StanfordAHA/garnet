#!/bin/bash

# Params
dataset=bcsstm26
# dataset=rand_large_tensor5

app=mat_elemadd3
# app=mat_elemmul
# app=mat_vecmul_ij
# app=matmul_ijk
# app=matmul_ikj
# app=tensor3_innerprod
# app=tensor3_mttkrp
# app=tensor3_ttm
# app=tensor3_ttv

python3 generate_sweep.py $app $dataset


