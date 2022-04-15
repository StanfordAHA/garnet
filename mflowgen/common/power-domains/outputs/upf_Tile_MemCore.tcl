######## Create Power Domains ###########
# Default Power Domain - SD when tile not used 
create_power_domain TOP -include_scope
#create_power_domain TOP
# AON Domain - Modules that stay ON when tile is OFF  
# PS configuration logic and tie cells for hi/lo outputs that drive the tile_id
create_power_domain AON -elements { PowerDomainOR DECODE_FEATURE_16 coreir_eq_16_inst0 and_inst1 FEATURE_AND_16 PowerDomainConfigReg_inst0 const_511_9 const_0_8}

### Toplevel Connections ######
## VDD 
create_supply_port VDD
create_supply_net  VDD -domain TOP
create_supply_net  VDD -domain AON -reuse

connect_supply_net VDD -ports  VDD

## VSS (0.0V)
create_supply_port VSS
create_supply_net  VSS -domain TOP
create_supply_net  VSS -domain AON -reuse

connect_supply_net VSS -ports  VSS

#### TOP SD Domain Power Connections ##########
create_supply_net VDD_SW -domain TOP 

#### Establish Connections ################
set_domain_supply_net AON -primary_power_net VDD -primary_ground_net VSS
set_domain_supply_net TOP -primary_power_net VDD_SW -primary_ground_net VSS

########### Set all Global Signals as AON
set_related_supply_net -object_list {tile_id hi lo clk reset config_config_addr config_config_data config_read config_write read_config_data_in stall flush} -power VDD -ground VSS
set_related_supply_net -object_list {clk_out reset_out config_out_config_addr config_out_config_data config_out_read config_out_write read_config_data stall_out flush_out} -power VDD -ground VSS


########### Create Shut-Down Logic for SD #######
create_power_switch SD_sw \
-domain TOP \
-input_supply_port {in VDD} \
-output_supply_port {out VDD_SW} \
-control_port {SD_sd PowerDomainConfigReg_inst0/read_config_data[0]} \
-on_state {ON_STATE in !SD_sd}

#### Create Power State Table ##################
add_port_state VDD -state {HighVoltage 0.8}
add_port_state SD_sw/out -state {HighVoltage 0.8} -state {SD_OFF off}
create_pst lvds_system_pst -supplies {VDD VDD_SW}
add_pst_state LOGIC_ON -pst lvds_system_pst -state {HighVoltage SD_OFF}
add_pst_state ALL_ON -pst lvds_system_pst -state {HighVoltage HighVoltage}
