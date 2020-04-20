# ALSO SEE 'post-rtl-filter.awk'

BEGIN { phase = "pre-rtl" }
{ date = strftime("%H:%M") }

# Stay in pre-rtl phase until see "rtl"

########################################################################
# PHASES triggered by "mkdir"
# Stay in "pre-rtl"
/mkdir.*rtl/         { phase = "rtl" }

# Post-rtl phases, not sposed to occur for this script's input!
/mkdir.*tsmc16/      { phase = "tsmc16"  }
/mkdir.*constraints/ { phase = "constraints"  }
/mkdir.*synthesis/   { phase = "synthesis"  }
/mkdir.*innovus/     { phase = "innovus" }
/mkdir.*calibre/     { phase = "calibre" }

# Heuristically mark the various 'make' phases
/^mkdir -p.*\/outputs/ {
    print "------------------------------------------------------------------------"
    print date " make " $3
    # print substr($0,0,72)
    next
}

########################################################################
# These messages always get to print regardless of phase
/^@file_info/ { print; next }

# This filter turns verbose mflowgen "make rtl" output
# into small summary file for buildkite log
# 
########################################################################
# Print all pre-rtl-phase output
phase == "pre-rtl" { print; next }

########################################################################
# Phase-independent checks

########################################
# Phase-dependent checks (none yet)

########################################
# RTL phase(s)
phase == "rtl" && /Genesis Is Starting/ { print substr($0, 5, 999); next }
phase == "rtl" && /Genesis Finished/    { print "" }
phase == "rtl" && /Starting code gener/ { print "  " $0; next }
# /Genesis Finished/    { print; next }
phase == "rtl" && /WARN/                { print "  " $0; next }
phase == "rtl" && /ERR/                 { print "  " $0; next }
phase == "rtl" && /^.pycoreir/          { print; next }
phase == "rtl" { next }
