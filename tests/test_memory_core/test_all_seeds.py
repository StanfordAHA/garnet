import shutil
import subprocess
import argparse
import os
import math
import time

all_tests = [
    "mat_elemadd",
    'mat_elemadd3',
    'mat_elemmul',
    'mat_identity',
    'mat_mattransmul',
    # # 'mat_residual',
    'mat_sddmm',
    # 'mat_vecmul_ij',
    # 'matmul_ijk',
    # 'matmul_jik',
    'tensor3_elemadd',
    'tensor3_elemmul',
    'tensor3_identity',
    'tensor3_innerprod',
    'tensor3_mttkrp',
    'tensor3_ttm',
    'tensor3_ttv',
    # 'vec_elemadd',
    # 'vec_elemmul',
    # 'vec_identity',
    # 'vec_scalar_mul',
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
         "./TESTING",
         "--dump_glb"],
        cwd=garnet_top
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Sparse TB Generator')
    # parser.add_argument('--sam_graph', type=str, default=None)
    parser.add_argument('--tests_dir', type=str, default=None)
    parser.add_argument('--run_dir', type=str, default=None)
    parser.add_argument('--sam_dir', type=str, default=None)
    parser.add_argument('--generate', action="store_true")
    parser.add_argument('--generate_vlog', action="store_true")
    parser.add_argument('--seeds', type=int, default=[0, 1], nargs=2)
    parser.add_argument('--parallel', type=int, default=1)

    args = parser.parse_args()
    tests_dir = args.tests_dir
    run_dir = args.run_dir
    generate = args.generate
    generate_vlog = args.generate_vlog
    sam_dir = args.sam_dir
    seed_range = args.seeds
    parallel = args.parallel

    seed_range_use = range(seed_range[0], seed_range[1])

    if generate:

        assert sam_dir is not None, "If generating, need to specify [--sam_dir <samdir>]"

        # seeds = range(0,

        subproc_args = ['python',
                        'tests/test_memory_core/build_tb.py',
                        '--ic_fork',
                        '--dump_bitstream',
                        '--add_pond',
                        '--combined',
                        '--pipeline_scanner',
                        '--base_dir',
                        f'{tests_dir}',
                        "--dump_glb",
                        "--fiber_access",
                        "--width",
                        "32",
                        "--height",
                        "16"]

        if generate_vlog:
            subproc_args.append("--gen_verilog")
            subproc_args.append("--gen_pe")

        subproc_args.append("--sam_graph")
        for test_ in all_tests:
            subproc_args.append(f"{sam_dir}/compiler/sam-outputs/dot/{test_}.gv")

        subproc_args.append("--seed")
        for seed_ in seed_range_use:
            # for seed_ in seeds:
            subproc_args.append(f"{seed_}")

            #         '--sam_graph',
            # f'../sam/compiler/sam-outputs/dot/{graph}.gv',
            # '--seed',
            # f'{seed}',

        subprocess.check_call(
            subproc_args,
            # cwd="./"
        )

        exit()

    print(tests_dir)
    print(run_dir)

    seed_range_use = range(seed_range[0], seed_range[1])

    if parallel > 1:

        t1 = time.time()

        all_procs = []
        print("doing parallel")
        chunk_size = math.ceil(len(seed_range_use) / parallel)
        for idx_ in range(parallel):
            num_to_use = chunk_size if (((idx_ + 1) * chunk_size) <= len(seed_range_use)) else (len(seed_range_use) - ((idx_) * chunk_size))
            local_seed_range = (idx_ * chunk_size, idx_ * chunk_size + num_to_use)
            print(f"Seed range for idx {idx_}: {local_seed_range}")
            print(local_seed_range)
            sim_dir_par = f"PARALLEL_SIM_DIR_{idx_}"
            if os.path.isdir(sim_dir_par):
                shutil.rmtree(sim_dir_par)
            shutil.copytree(run_dir, sim_dir_par)
            logfile_ = f"log_file_{idx_}.txt"
            logfile_e = f"log_file_{idx_}_error.txt"
            with open(logfile_, 'w+') as tmp_fh:
                with open(logfile_e, 'w+') as tmp_fh_e:
                    p_ = subprocess.Popen(
                        ['python',
                         './tests/test_memory_core/test_all_seeds.py',
                         '--tests_dir',
                         f'{tests_dir}',
                         f'--run_dir',
                         f'{sim_dir_par}',
                         '--seeds',
                         f'{local_seed_range[0]}',
                         f'{local_seed_range[1]}'],
                        stdout=tmp_fh,
                        stderr=tmp_fh_e,
                        cwd="./")
                    all_procs.append(p_)

        for proc_ in all_procs:
            proc_.wait()
        t2 = time.time()
        print(f"PARALLEL TIME : P={parallel}: {t2 - t1}")

    else:

        print(tests_dir)
        t1 = time.time()

        for test_ in os.listdir(tests_dir):
            seed = int(test_.split('_')[-1])
            if seed in seed_range_use:
                full_path = f"{tests_dir}/{test_}"

                subprocess.check_call(
                    ['make',
                     'run',
                     f'TEST_DIR={os.path.abspath(full_path)}'],
                    cwd=run_dir
                )

        t2 = time.time()
        print(f"SERIAL TIME : {t2 - t1}")
