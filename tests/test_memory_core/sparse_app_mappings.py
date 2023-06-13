from sam.onyx.generate_matrices import MatrixGenerator, get_tensor_from_files
import os
from sam.sim.test.test import read_inputs


def get_tensor(input_name=None, shapes=None, give_tensor=False,
               tmp_dir=None, dump=None, suffix="", clean=False, tensor_ordering=None, sparsity=None,
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
