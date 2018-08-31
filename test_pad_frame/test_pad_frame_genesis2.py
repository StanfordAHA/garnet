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
        "--tile_id_offset", "32",
        "pad_frame/genesis/io1bit.vp",
        "pad_frame/genesis/io_group.svp",
        "pad_frame/genesis/pad_frame.svp"
    ]
    pad_frame_genesis2.memory_core_wrapper.main(
        argv=argv)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top memory_core -input memory_core/genesis/input_sr.vp memory_core/genesis/output_sr.vp memory_core/genesis/linebuffer_control.vp memory_core/genesis/fifo_control.vp memory_core/genesis/mem.vp memory_core/genesis/memory_core.vp -parameter memory_core.dwidth='16' -parameter memory_core.ddepth='1024''
memory_core(clk_in: In(Bit), clk_en: In(Bit), reset: In(Bit), config_addr: Array(32,In(Bit)), config_data: Array(32,In(Bit)), config_read: In(Bit), config_write: In(Bit), config_en: In(Bit), config_en_sram: Array(4,In(Bit)), config_en_linebuf: In(Bit), data_in: Array(16,In(Bit)), data_out: Array(16,Out(Bit)), wen_in: In(Bit), ren_in: In(Bit), valid_out: Out(Bit), chain_in: Array(16,In(Bit)), chain_out: Array(16,Out(Bit)), chain_wen_in: In(Bit), chain_valid_out: Out(Bit), almost_full: Out(Bit), almost_empty: Out(Bit), addr_in: Array(16,In(Bit)), read_data: Array(32,Out(Bit)), read_data_sram: Array(32,Out(Bit)), read_data_linebuf: Array(32,Out(Bit)), flush: In(Bit))
"""  # nopep8
