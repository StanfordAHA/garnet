import tempfile
import os
import json
from global_buffer.global_buffer_magma import GlobalBuffer
from global_buffer.global_buffer_bs_generator import Glb


def test_all_glb_config_register():
    global_buffer = GlobalBuffer(num_banks=32,
                                 num_io=8,
                                 num_cfg=8,
                                 bank_addr_width=17,
                                 glb_addr_width=32,
                                 cfg_addr_width=32,
                                 cfg_data_width=32,
                                 axi_addr_width=12)
    glb = Glb(global_buffer)

    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "glb_config.json")
        result = glb.dump_all_config()
        with open(filename, "w+") as f:
            json.dump(result, f)


def test_glb_bs_gen():
    global_buffer = GlobalBuffer(num_banks=32,
                                 num_io=8,
                                 num_cfg=8,
                                 bank_addr_width=17,
                                 glb_addr_width=32,
                                 cfg_addr_width=32,
                                 cfg_data_width=32,
                                 axi_addr_width=12)
    glb = Glb(global_buffer)
    dummy_collateral = (("in", 16), ("out", 16))
    bitstream = glb.config(dummy_collateral)

    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "glb_bs.bs")
        with open(filename, "w+") as f:
            bs = ["{0:03X} {1:08X}".format(entry[0], entry[1]) for entry
                  in bitstream]
            f.write("\n".join(bs))
