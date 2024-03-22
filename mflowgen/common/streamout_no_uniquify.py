def streamout_no_uniquify(iflow):
    '''Remove uniquify flag from stream-out.tcl'''

    # Before remove_script runs, stream-out.tcl contains:
    #   streamOut $vars(results_dir)/$vars(design)-merged.gds \
    #     -units 1000 \
    #     -mapFile $vars(gds_layer_map) \
    #     -uniquifyCellNames \
    #     -merge $merge_files
    #
    # After script runs:
    #   streamOut $vars(results_dir)/$vars(design)-merged.gds \
    #     -units 1000 \
    #     -mapFile $vars(gds_layer_map) \
    #     -merge $merge_files

    # Add removal instructions to iflow step list of 'mflowgen-run' commands
    script = "innovus-foundation-flow/custom-scripts/stream-out.tcl"

    remove_script = f'''
      echo "--- BEGIN EGREGIOUS HACK to undo mflowgen default -uniquify"
      echo -n "BEFORE: "; grep uniq {script} || echo okay
      grep -v uniquifyCellNames {script} > tmp-stream-out
      mv tmp-stream-out {script}
      echo -n "AFTER: "; grep uniquifyCellNames {script} || echo okay
    '''

    # Make a list
    rs_list = remove_script.split("\n")

    # Reverse it, because of how "prepend" works, duh.
    rs_list.reverse()

    # Prepend the commands to the script
    # for cmd in remove_script.split("\n"):
    for cmd in rs_list:
        if cmd.strip():
            iflow.pre_extend_commands([cmd.strip()])
