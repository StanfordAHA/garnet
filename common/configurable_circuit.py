import magma as m


def ConfigInterface(config_addr_width, config_data_width):
    return [
        "config_addr", m.In(m.Bits(config_addr_width)),
        "config_data", m.In(m.Bits(config_data_width)),
        "config_en", m.In(m.Enable),
        "read_data", m.Out(m.Bits(config_data_width))
    ]
