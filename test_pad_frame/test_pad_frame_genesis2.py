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
        "pad_frame/genesis/io1bit.vp",
        "pad_frame/genesis/fixed_io.vp"
    ]
    pad_frame_genesis2.pad_frame_wrapper.main(argv=argv)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top pad_frame -input pad_frame/genesis/pad_frame.vp pad_frame/genesis/io_group.vp pad_frame/genesis/io1bit.vp pad_frame/genesis/fixed_io.vp -parameter pad_frame.num_ios_per_group='16' -parameter pad_frame.num_groups_per_side='1' -parameter pad_frame.config_addr_width='32' -parameter pad_frame.config_data_width='32' -parameter pad_frame.tile_id_offset='400''
pad_frame(clk_pad: In(Bit), reset_pad: In(Bit), tck_pad: In(Bit), tms_pad: In(Bit), tdi_pad: In(Bit), trst_n_pad: In(Bit), tdo_pad: Out(Bit), config_data: In(Bits(32)), config_addr: In(Bits(32)), config_read: In(Bit), config_write: In(Bit), clk: Out(Bit), reset: Out(Bit), tck: Out(Bit), tdi: Out(Bit), tms: Out(Bit), trst_n: Out(Bit), tdo: In(Bit), f2p_wide_N_0: In(Bits(16)), f2p_1bit_N_0: In(Bits(16)), pads_N_0: Bits(16), p2f_N_0: Out(Bits(16)), f2p_wide_E_0: In(Bits(16)), f2p_1bit_E_0: In(Bits(16)), pads_E_0: Bits(16), p2f_E_0: Out(Bits(16)), f2p_wide_S_0: In(Bits(16)), f2p_1bit_S_0: In(Bits(16)), pads_S_0: Bits(16), p2f_S_0: Out(Bits(16)), f2p_wide_W_0: In(Bits(16)), f2p_1bit_W_0: In(Bits(16)), pads_W_0: Bits(16), p2f_W_0: Out(Bits(16)), read_data: Out(Bits(32)))
"""  # nopep8
