from verified_agile_hardware.yosys_utils import garnet_tile_to_btor
from verified_agile_hardware.solver import Solver
import os

def verify_bitstream(interconnect, coreir_file, instance_to_instr):
    app_dir = os.path.dirname(coreir_file)

    solver = Solver()
    solver.app_dir = f"{app_dir}/verification"
    
    if not os.path.exists(solver.app_dir):
        os.mkdir(solver.app_dir)

    garnet_tile_to_btor(app_dir=solver.app_dir)
