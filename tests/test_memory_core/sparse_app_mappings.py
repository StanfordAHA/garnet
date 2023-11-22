from sam.onyx.generate_matrices import MatrixGenerator, get_tensor_from_files
import os
import numpy as np
from sam.sim.test.test import read_inputs
from lassen.tlut import tlut


def get_tensor(input_name=None, shapes=None, give_tensor=False,
               tmp_dir=None, dump=None, suffix="", clean=False, tensor_ordering=None, sparsity=0.7,
               format='CSF'):

    if give_tensor:
        assert tmp_dir is not None
        assert tensor_ordering is not None
        shape_ = read_inputs(os.path.join(tmp_dir, f"tensor_{input_name}_mode_shape"))
        matrix_gen = get_tensor_from_files(name=input_name, files_dir=tmp_dir, shape=shape_, base=10, early_terminate='x',
                                           tensor_ordering=tensor_ordering)
    else:
        assert dump is not None
        assert shapes is not None
        matrix_gen = MatrixGenerator(name=input_name, shape=shapes, sparsity=sparsity,
                                     format=format, dump_dir=dump, clean=clean)
        matrix_gen.dump_outputs(suffix=suffix)

    ret_mat = matrix_gen.get_matrix()

    return ret_mat

def get_lut_tensor(dump=None, suffix="", clean=False, func=None):
    assert func is not None, "Please specify the complex ops function to load into memory"
    assert dump is not None, "Please specify the directory to dump the matrix"

    lut_mat = []
    # generate matrix base on the specified function
    TLUT = tlut()
    if func == 'exp':
        lut_mat += [TLUT.exp_lut(i) for i in range(0, 128)] + [TLUT.exp_lut(i) for i in range(-128, 0)]
    else:
        raise NotImplementedError("unkown complex op function for preloading memory")
    lut_mat_np = np.array(lut_mat)

    matrix_gen = MatrixGenerator(name=func, shape=[len(lut_mat)], sparsity=0.0,
                                 format='UNC', dump_dir=dump, clean=clean, tensor=lut_mat_np)
    matrix_gen.dump_outputs(suffix=suffix)

    ret_mat = matrix_gen.get_matrix()

    return ret_mat


