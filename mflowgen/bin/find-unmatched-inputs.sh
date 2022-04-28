#!/bin/bash

if [ "$1" == "--help" ]; then
  cat <<EOF
    DESCRIPTION:
    Look at indicated mflowgen graph datafile and
    see if there are umatched inputs on any node

    EXAMPLE:
    % $0 16-glb_top/.mflowgen/graph.dot
    WARNING found unconnected output edge   mentor_calibre_drc     / <drc_summary>
    WARNING found unconnected output edge   mentor_calibre_lvs     / <lvs_report>

    ERROR found unconnected input edge   cadence_innovus_debug_calibre / <lvs_results>

EOF
fi

infile=$1
cat $infile | awk '
  function process_edge(edgetype) {
    edgename = substr($i, 4, 999) 
    all_edges[edgename] = 1
    node[edgename] = nodename
    if (DBG)  print "  " $i
    if (DBG9) printf("EDGENAME .%s.\n", edgename)
    if (edgetype == "input")  n_input_conn[ edgename]++
    if (edgetype == "output") n_output_conn[edgename]++
  }

  { DBG = 0; DBG9 = 0 }
  DBG { print "FOO1 " $0 }
  /:/ { next } # skip the actual graph-connection part

  # node name
  / fontsize/ { nodename = $1;  if (DBG) print "\n" nodename }

  # inputs
  /i_/ { if (DBG) print "FOO2 " $0
    if (DBG) print "  INPUTS"
    for (i=1; i<=NF; i++) if ($i ~ /^</) process_edge("input")
  }

  # outputs
  /o_/ { if (DBG) print "FOO3 " $0
    if (DBG) print "  OUTPUTS"
    for (i=1; i<=NF; i++) if ($i ~ /^</) process_edge("output")
  }

  END { 
    for (edgename in all_edges) {
      e = edgename; s = status[e]; n = node[e]
      ins = n_input_conn[e]; outs = n_output_conn[e]

      if (ins && !outs) {

          # IGNORE this error for now
          # FIXME/TODO file an issue on this problem
          # FIXME/TODO make a "--ignore" switch for this script

          if (n == "cadence_innovus_debug_calibre" && e == "lvs_results>") {
              fmt="WARNING ignoring unconnected input edge   %-22s / <%s\n"
              ignores=ignores sprintf(fmt, n, e)
              continue
          }
          fmt="ERROR found unconnected input edge   %-22s / <%s\n"
          errs=errs sprintf(fmt, n, e)
      }
      else if (outs && !ins) {
          fmt="WARNING found unconnected output edge   %-22s / <%s\n"
          warns=warns sprintf(fmt, n, e)
      }
      else if (!outs && !ins) {
          print "ERROR ooh somethings ripped, this should never happen"
          exit(13)
      }
      else { if (DBG) { printf("OKAY edge has %d ins and %d outs\n", ins, outs) } }
    }

    print warns   | "sort"; close("sort")
    print ignores | "sort"; close("sort")
    print errs    | "sort"; close("sort")
    if (errs) exit(13)
  }
'
