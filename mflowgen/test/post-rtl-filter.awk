# This filter turns million-line mflowgen output
# into small summary file for buildkite log
# 
BEGIN { phase = "unknown" }
{ date = strftime("%H:%M") }

########################################################################
# Always pass the following strings:
/STILL UNCONNECTED: [Bb]ump/ { print; next }


########################################################################
# PHASES triggered by "mkdir"

# rtl phase (not sposed to occur for this script's input)
/mkdir.*rtl/         { phase = "rtl" }     # Not supposed to happen!

# Post-rtl phases
/mkdir.*tsmc16/      { phase = "tsmc16"  } # First stage after rtl maybe
/mkdir.*constraints/ { phase = "constraints"  }
/mkdir.*synthesis/   { phase = "synthesis"  }
/mkdir.*innovus/     { phase = "innovus" }
/mkdir.*drc/         { phase = "drc" }

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
# Allow e.g. "+++ @file_info" (kind of a hack, like this entire file!)
/^--- @file_info/ { print; next }
/^+++ @file_info/ { print; next }


########################################################################
# Annoyingly, lines starting with '--- ' or '+++ ' are control sequences
# for buildkite log...this rewrites those lines to prevent that
/^--- / { $0 = "-- " substr($0, 4, 999); print $0; next }
/^+++ / { $0 = "++ " substr($0, 4, 999); print $0; next }

########################################################################
# Print end matter from calibre drc check; but not too much
/EXECUTIVE MODULE COMPLETED/ { printremaining = 1 }
printremaining==1 && /PROCESS WAS STOPPED/ { printremaining=0 }
printremaining==1 { print; next }

########################################################################
# Phase-independent checks

# Failed assertions e.g. 
#   FAILED mflowgen-check-postconditions.py::test_2_ - AssertionError: assert 'er...
#   FAILED mflowgen-check-postconditions.py::test_3_ - AssertionError: assert 'Un...
#   FAILED mflowgen-check-postconditions.py::test_4_ - AssertionError: assert 'Un...
#   FAILED mflowgen-check-postconditions.py::test_6_ - AssertionError: assert 'cr...
/^  FAILED mflowgen/ { print; next; }

# Pytest info e.g.
#  pytest -q -rA --disable-warnings --tb=short --color=yes ./mflowgen-check-postconditions.py
#  ..FFF.F.                                                                 [100%]<ctl-chars>
# Note ctl-chars for colors :( e.g. "[100%]^[[0m"
/^pytest/ { print ""; print; next }
/%]...m$/ { print; next }


########################################################
# These are technically specific to innovus phase(s)
# Design Stage: PreRoute
# Design Name: Tile_PE
# Design Mode: 16nm
# Analysis Mode: MMMC Non-OCV 
# Parasitics Mode: No SPEF/RCDB
# Signoff Settings: SI Off 
# { print }
/^# Design Stage/     { $1=""; $2=""; $3=""; info = $0 }
/^# Design Name/      { $1=""; $2=""; $3=""; info = info " - " $0 }
/^# Design Mode/      { $1=""; $2=""; $3=""; info = info " - " $0 }
/^# Analysis Mode/    { $1=""; $2=""; $3=""; info = info " - " $0 }
/^# Parasitics Mode/  { $1=""; $2=""; $3=""; info = info " - " $0 }
/^# Signoff Settings/ { $1=""; $2=""; $3=""; info = info " - " $0; print date " " info }
# 
# Timing info
# +--------------------+---------+---------+---------+---------+
# |     Setup mode     |   all   | reg2reg |reg2cgate| default |
# +--------------------+---------+---------+---------+---------+
# |           WNS (ns):|  1.801  |  6.648  |  9.813  |  1.801  |
# |           TNS (ns):|  0.000  |  0.000  |  0.000  |  0.000  |
# |    Violating Paths:|    0    |    0    |    0    |    0    |
# |          All Paths:|  1346   |   495   |    2    |  1346   |
# +--------------------+---------+---------+---------+---------+
/(Setup|Hold) mode/   { print ""; print $0 }
/WNS..ns/             { print $0; print "" }


################################################################
# These are technically specific to calibre phase(s)
/MODULE.*COMPLETED/ { print; print ""; next; }
/MODULE/ { print; next }
/Calibre v/ { print; print ""; next }
/Rule file generated/   { print; next }
/OPS COMPLETE.*000\ OF/ { print; next }


########################################################################
# Phase-dependent checks

########################################
# INNOVUS phase(s)
phase == "innovus" && /ERROR/ { print; next }
phase == "innovus" && /^Cadence|^Version/  { print; next }
phase == "innovus" && /Sourcing|starts at/ {
    # Believe it or not sometimes get multiple identical lines w/same time stamp etc
    if ($0 == prev_source_start) { next }
    prev_source_start = $0
    print ""; print $0; next
}

