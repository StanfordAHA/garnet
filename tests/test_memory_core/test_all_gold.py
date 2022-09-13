import subprocess

all_tests = [
    "mat_elemadd",
    'mat_elemadd3',
    'mat_elemmul',
    'mat_identity',
    'mat_mattransmul',
    # 'mat_residual',
    'mat_sddmm',
    'mat_vecmul_ij',
    'matmul_ijk',
    'matmul_jik',
    'tensor3_elemadd',
    'tensor3_elemmul',
    'tensor3_identity',
    'tensor3_innerprod',
    'tensor3_mttkrp',
    'tensor3_ttm',
    'tensor3_ttv',
    'vec_elemadd',
    'vec_elemmul',
    'vec_identity',
    'vec_scalar_mul',
    'vec_spacc_simple',
]


def dispatch(garnet_top=None, graph="", seed=0):
    subprocess.check_call(
        ['python',
         'tests/test_memory_core/build_tb.py',
         '--ic_fork',
         '--sam_graph',
         f'../sam/compiler/sam-outputs/dot/{graph}.gv',
         '--seed',
         f'{seed}',
         '--trace',
         '--dump_bitstream',
         '--add_pond',
         '--combined',
         '--pipeline_scanner',
         '--base_dir',
         "./TESTING"],
        cwd=garnet_top
    )


if __name__ == "__main__":

    seeds = [0, 1, 2]

    for test in all_tests:
        for seed in seeds:
            print(f"RUNNING TEST: TESTNAME: {test}")
            print(f"RUNNING TEST: SEED: {seed}")
            dispatch(garnet_top='/home/max/Documents/SPARSE/garnet/',
                     graph=test, seed=seed)
