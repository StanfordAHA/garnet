#! /bin/bash
mkdir -p reports logs

# We check for the batch mode and execute the power flow over a set of files
# instead of using the basic 1-shot flow
if [ $batch = "True" ]; then
  # Create base strip path, then read through each relevant file
  export base_strip_path=${strip_path}
  for tile_file in $(ls inputs/ | grep 'list_*')
  do
    echo "Processing file: ${tile_file}"
    export design_name=$(echo $tile_file | sed 's|tiles_||g' | sed 's|.list||g')
    echo "Design name is: ${design_name}"
    pushd inputs
    for design_file in $(ls ${design_name}*)
    do
      # Kill original so we don't screw things up backwards
      repl_name=$(echo ${design_file} | sed "s|${design_name}|design|g")
      if [ -f $repl_name ]; then
        rm $repl_name
      fi
      cp -L $design_file $repl_name
    done
    popd
    while read p
    do
      export tile_name=$(echo $p | awk -F, '{printf "Tile_X%s_Y%s\n",$2,$3}')
      export tile_alias=$(echo $p | awk -F, '{print $1}')
      echo "Tile coordinates: ${tile_name}"
      echo "Tile name: ${tile_alias}"
      export strip_path="${base_strip_path}/${tile_name}"
      pt_shell -f ptpx.tcl | tee logs/pt_${design_name}_${tile_alias}_${tile_name}.log
      cp reports/${design_name}_${tile_alias}_${tile_name}.power.hier.rpt outputs/power_${design_name}_${tile_alias}_${tile_name}.hier
      cp reports/${design_name}_${tile_alias}_${tile_name}.power.cell.rpt outputs/power_${design_name}_${tile_alias}_${tile_name}.cell
    done < inputs/$tile_file
  done 
else 
  pt_shell -f ptpx.tcl | tee logs/pt.log
  cp reports/${design_name}.power.hier.rpt outputs/power.hier
  cp reports/${design_name}.power.cell.rpt outputs/power.cell
fi
