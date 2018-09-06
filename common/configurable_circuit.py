import magma as m


def ConfigInterface(config_addr_width, config_data_width):
    return [
        "config_addr", m.In(m.Bits(config_addr_width)),
        "config_data", m.In(m.Bits(config_data_width)),
        "config_en", m.In(m.Enable),
        "read_data", m.Out(m.Bits(config_data_width))
    ]


config_ets_template = """\
# INIT
I: self.reset = 0_1
I: self.config_en = 0_1
I: conf_done = 0_1
I: self.config_addr = 0_{config_addr_width}
I: self.config_data = 0_{config_data_width}

# STATES


# S0 -> S0a: reset
S0: self.config_addr = 0_{config_addr_width}
S0: self.config_data = 0_{config_data_width}
S0: self.config_en = 0_1
S0: self.reset = 0_1
S0: conf_done = 0_1

S0a: self.config_addr = 0_{config_addr_width}
S0a: self.config_data = 0_{config_data_width}
S0a: self.config_en = 0_1
S0a: self.reset = 1_1
S0a: conf_done = 0_1

S1: self.config_addr = 0_{config_addr_width}
S1: self.config_data = 0_{config_data_width}
S1: self.config_en = 0_1
S1: self.reset = 0_1
S1: conf_done = 0_1

# S1a -> S2a: config
S1a: self.config_addr = {config_addr}_{config_addr_width}
S1a: self.config_data = {config_data}_{config_data_width}
S1a: self.config_en = 1_1
S1a: self.reset = 0_1
S1a: conf_done = 0_1

S2: self.config_addr = {config_addr}_{config_addr_width}
S2: self.config_data = {config_data}_{config_data_width}
S2: self.config_en = 1_1
S2: self.reset = 0_1
S2: conf_done = 0_1

S2a: self.config_addr = 0_{config_addr_width}
S2a: self.config_data = 0_{config_data_width}
S2a: self.config_en = 0_1
S2a: self.reset = 0_1
S2a: conf_done = 1_1

# TRANSITIONS
I -> S0
S0 -> S0a
S0a -> S1
S1 -> S1a
S1a -> S2
S2 -> S2a
S2a -> S2a
"""
