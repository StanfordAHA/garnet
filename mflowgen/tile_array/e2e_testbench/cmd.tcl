##############
# Dump waves #
##############
if { $::env(waves) == "True" } {
  database -shm -default waves
  probe -shm Interconnect_tb -depth all -all
}
##############
# Saif front #
##############
dumpsaif -scope Interconnect_tb -hierarchy -internal -output outputs/run.saif -overwrite

###########
# Runtime #
###########
run

############
# Saif end #
############
dumpsaif -end

#
quit
