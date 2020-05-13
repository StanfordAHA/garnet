# ==============================================================================
# loads CGRA design files (RTL)
# ==============================================================================

# Garnet Files
set cgra_garnet_files [
  glob -nocomplain -directory inputs -types f *.v *.sv]

# All CGRA Files
set cgra_design_files [concat \
  $cgra_garnet_files ]
