def streamout_no_uniquify(iflow):
  '''Remove uniquify flag from stream-out.tcl'''

  # Add removal instructions to iflow step list of 'mflowgen-run' commands
  script = "innovus-foundation-flow/custom-scripts/stream-out.tcl"
  remove_script = f'''
    echo "--- BEGIN EGREGIOUS HACK to undo mflowgen default -uniquify"
    echo -n "BEFORE: "; grep uniq {script} || echo okay
    grep -v uniq {script} > tmp-stream-out
    mv tmp-stream-out {script}
    echo -n "AFTER: "; grep uniq {script} || echo okay
  '''
  # Make a list
  rs_list = remove_script.split("\n")

  # Reverse it, because of how "prepend" works, duh.
  rs_list.reverse()

  # Prepend the commands to the script
  # for cmd in remove_script.split("\n"):
  for cmd in rs_list:
    if cmd.strip(): iflow.pre_extend_commands( [ cmd.strip() ] )
