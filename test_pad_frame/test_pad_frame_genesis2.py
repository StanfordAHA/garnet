from pad_frame import pad_frame_genesis2
import glob
import os


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


def test_main(capsys):
    argv = [
        "--config_data_width", "32",
        "--config_addr_width", "32",
        "--num_ios_per_group", "16",
        "--num_groups_per_side", "1",
        "--tile_id_offset", "400",
        "pad_frame/genesis/pad_frame.vp",
        "pad_frame/genesis/io_group.vp",
        "pad_frame/genesis/io1bit.vp"
    ]
    pad_frame_genesis2.pad_frame_wrapper.main(
        argv=argv)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top pad_frame -input pad_frame/genesis/pad_frame.vp pad_frame/genesis/io_group.vp pad_frame/genesis/io1bit.vp -parameter pad_frame.num_ios_per_group='16' -parameter pad_frame.num_groups_per_side='1' -parameter pad_frame.config_addr_width='32' -parameter pad_frame.config_data_width='32' -parameter pad_frame.tile_id_offset='400''
pad_frame(clk: In(Bit), reset: In(Bit), config_data: Array(32,In(Bit)), config_addr: Array(32,In(Bit)), config_read: In(Bit), config_write: In(Bit), f2p_wide_N_0: Array(16,In(Bit)), f2p_1bit_N_0: Array(16,In(Bit)), pads_N_0: Array(16,InOut(Bit)), p2f_N_0: Array(16,Out(Bit)), f2p_wide_E_0: Array(16,In(Bit)), f2p_1bit_E_0: Array(16,In(Bit)), pads_E_0: Array(16,InOut(Bit)), p2f_E_0: Array(16,Out(Bit)), f2p_wide_S_0: Array(16,In(Bit)), f2p_1bit_S_0: Array(16,In(Bit)), pads_S_0: Array(16,InOut(Bit)), p2f_S_0: Array(16,Out(Bit)), f2p_wide_W_0: Array(16,In(Bit)), f2p_1bit_W_0: Array(16,In(Bit)), pads_W_0: Array(16,InOut(Bit)), p2f_W_0: Array(16,Out(Bit)), read_data: Array(32,Out(Bit)))
"""  # nopep8
