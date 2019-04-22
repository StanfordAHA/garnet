######## Create Power Domains ###########
# Default Power Domain - SD when tile not used 
create_power_domain TOP -include_scope
#create_power_domain TOP
# AON Domain - Modules that stay ON when tile is OFF  
#create_power_domain AON -elements {iso_en ps_en}
create_power_domain AON -elements {ps_en}

### Toplevel Connections ######
## VDD_HIGH 
create_supply_port VDD_HIGH
create_supply_net  VDD_HIGH -domain TOP
create_supply_net  VDD_HIGH -domain AON -reuse

connect_supply_net VDD_HIGH -ports  VDD_HIGH

## VSS (0.0V)
create_supply_port VSS
create_supply_net  VSS -domain TOP
create_supply_net  VSS -domain AON -reuse

connect_supply_net VSS -ports  VSS

#### TOP SD Domain Power Connections ##########
create_supply_net VDD_HIGH_TOP_VIRTUAL -domain TOP 

#### Establish Connections ################
set_domain_supply_net AON -primary_power_net VDD_HIGH -primary_ground_net VSS
set_domain_supply_net TOP -primary_power_net VDD_HIGH_TOP_VIRTUAL -primary_ground_net VSS

########### Create Shut-Down Logic for SD #######
create_power_switch SD_sw \
-domain TOP \
-input_supply_port {in VDD_HIGH} \
-output_supply_port {out VDD_HIGH_TOP_VIRTUAL} \
-control_port {SD_sd ps_en/O[0]} \
-on_state {ON_STATE in !SD_sd}

#### Iso Cells #######
#set_isolation iso_out \
#-domain TOP \
#-isolation_power_net VDD_HIGH -isolation_ground_net VSS \
#-clamp_value 0 \
#-applies_to outputs 
#
#set_isolation_control iso_out \
#-domain TOP \
#-isolation_signal iso_en/O[0] \
#-isolation_sense low \
#-location self 

#### Create Power State Table ##################
add_port_state VDD_HIGH -state {HighVoltage 0.7}
add_port_state SD_sw/out -state {HighVoltage 0.7} -state {SD_OFF off}
create_pst lvds_system_pst -supplies {VDD_HIGH VDD_HIGH_TOP_VIRTUAL}
add_pst_state LOGIC_ON -pst lvds_system_pst -state {HighVoltage SD_OFF}
add_pst_state ALL_ON -pst lvds_system_pst -state {HighVoltage HighVoltage}
