# INIT
I: self.reset = 0_1
I: self.config_en = 0_1
I: conf_done = 0_1
I: self.config_addr = 0_1
I: self.config_data = 0_2

# STATES


# S0 -> S0a: reset
S0: self.config_addr = 0_1
S0: self.config_data = 0_2
S0: self.config_en = 0_1
S0: self.reset = 0_1
S0: conf_done = 0_1

S0a: self.config_addr = 0_1
S0a: self.config_data = 0_2
S0a: self.config_en = 0_1
S0a: self.reset = 1_1
S0a: conf_done = 0_1

S1: self.config_addr = 0_1
S1: self.config_data = 0_2
S1: self.config_en = 0_1
S1: self.reset = 0_1
S1: conf_done = 0_1

# S1a -> S2a: config
S1a: self.config_addr = 0_1
S1a: self.config_data = 0_2
S1a: self.config_en = 1_1
S1a: self.reset = 0_1
S1a: conf_done = 0_1

S2: self.config_addr = 0_1
S2: self.config_data = 0_2
S2: self.config_en = 1_1
S2: self.reset = 0_1
S2: conf_done = 0_1

S2a: self.config_addr = 0_1
S2a: self.config_data = 0_2
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
