import magma as m
from gemstone.generator.generator import set_debug_mode
from global_buffer.global_buffer_magma import GlobalBuffer


# set the debug mode to false to speed up construction
set_debug_mode(False)


def main():
    width = 4

    # configuration parameters
    config_addr_width = 32
    config_data_width = 32
    axi_addr_width = 12
    axi_data_width = 32
    # axi_data_width must be same as cgra config_data_width
    assert axi_data_width == config_data_width

    tile_id_width = 16
    config_addr_reg_width = 8
    num_tracks = 5

    num_glb_tiles = width // 2

    bank_addr_width = 17
    bank_data_width = 64
    banks_per_tile = 2

    glb_addr_width = (bank_addr_width
                      + m.bitutils.clog2(banks_per_tile)
                      + m.bitutils.clog2(num_glb_tiles))

    # bank_data_width must be the size of bitstream
    assert bank_data_width == config_addr_width + config_data_width

    global_buffer = GlobalBuffer(num_glb_tiles=num_glb_tiles,
                                 num_cgra_cols=width,
                                 bank_addr_width=bank_addr_width,
                                 bank_data_width=bank_data_width,
                                 cfg_addr_width=config_addr_width,
                                 cfg_data_width=config_data_width,
                                 axi_addr_width=axi_addr_width,
                                 axi_data_width=axi_data_width)

    circuit = global_buffer.circuit()
    m.compile("global_buffer", circuit, output="coreir-verilog")


if __name__ == "__main__":
    main()
