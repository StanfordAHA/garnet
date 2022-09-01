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


def dispatch(garnet_top=None, graph=""):
    subprocess.check_call(
        ['python',
         'tests/test_memory_core/build_tb.py',
         '--ic_fork',
         '--sam_graph',
         f'../sam/compiler/sam-outputs/dot/{graph}.gv',
         '--output_dir',
         '/home/max/Documents/SPARSE/garnet/mek_outputs/',
         '--input_dir',
         '/home/max/Documents/SPARSE/garnet/final_mat/',
         '--test_dump_dir',
         './mek_dump',
         '--matrix_tmp_dir',
         'tmp_mat/',
         '--seed',
         '0',
         '--trace',
         '--gold_dir',
         'gold_out/',
         '--fifo_depth',
         '8',
         '--gen_pe',
         '--dump_bitstream',
         '--add_pond',
         '--combined',
         '--pipeline_scanner'], cwd=garnet_top
    )


if __name__ == "__main__":

    for test in all_tests:
        print(f"RUNNING TEST: {test}")
        dispatch(garnet_top='/home/max/Documents/SPARSE/garnet/',
                 graph=test)
