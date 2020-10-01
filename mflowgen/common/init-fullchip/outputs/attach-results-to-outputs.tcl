# prev step "stream-out.tcl puts gds output in "results/<design_name>.gds.gz"
# 
# steps/cadence-innovus-flowsetup/innovus-foundation-flow/custom-scripts/stream-out.tcl
#   streamOut $vars(results_dir)/$vars(design).gds.gz -units 1000 -mapFile $vars(gds_layer_map)
#
# But to be useful for the next step, gds must be available as "outputs/design.gds.gz".
# Hence this script:

cd outputs
  # ln -sf ../$vars(results_dir)/$vars(design).gds.gz design.gds.gz
  # Oops no what if $vars(results_dir is absolute path?
  # Must embed assumptions and/or build better script. For now choose the former.
  ln -sf ../results/$vars(design)-merged.gds design-merged.gds
cd ..
