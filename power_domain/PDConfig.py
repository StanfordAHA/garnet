# ---------------------------------
# Configurations for Power Domains
# --------------------------------


class PDCGRAConfig:
    def __init__(self):
        # -----------------------
        # GLOBAL
        # -----------------------
        # Enable Low Power Design
        self.en_power_domains = 1
        # Power domain boundary.
        # The domain type changes from the boundary value specified
        self.pd_bndry_loc = 0
        # ----------------------
        # POWER SWITCHES
        # ----------------------
        # PS insertion location; 0:RTL; 1:Backend
        self.ps_loc = 1
        # PS connection pattern; 0:Daisy Chain; 1:Fanout
        self.connection = 0
        # PS count per SD domain
        self.ps_count = 10
        # Cfg reg name for PS en
        self.ps_config_name = "ps_en"
        # Cfg reg addr for PS en
        self.cfg_reg_addr_ps = 30
        # -----------------------
        # ISO CELLS
        # -----------------------
        # Isolation strategy;
        # 0: Mux Transform
        # 1: ISO cells on one side
        # 2: ISO cells on all sides
        self.iso_strategy = 0 
        # Cfg reg name for ISO en
        self.iso_config_name = "iso_en"
        # Cfg reg addr for ISO en
        self.cfg_reg_addr_iso = 31
        self.use_aoi = (self.iso_strategy == 0) and (self.en_power_domains == 1)
