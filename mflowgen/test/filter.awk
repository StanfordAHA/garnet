BEGIN { phase = "pre-rtl" }
{ date = strftime("%H:%M") }

########################################################################
# PHASES triggered by "mkdir"
/mkdir.*rtl/     { phase = "rtl"     }
/mkdir.*innovus/ { phase = "innovus" }
/mkdir.*calibre/ { phase = "calibre" }
/^mkdir -p/ {
    print "------------------------------------------------------------------------"
    print date " make " $3
    # print substr($0,0,72)
    next
}


########################################################################
# Print all pre-rtl-phase output
phase == "pre-rtl" { print; next }


########################################################################
# Print end matter from calibre drc check; but not too much
/EXECUTIVE MODULE COMPLETED/ { printremaining = 1 }
printremaining==1 && /PROCESS WAS STOPPED/ { printremaining=0 }
printremaining==1 { print; next }


########################################################################
# Phase-independent checks

########################################################
# These are technically specific to innovus phase
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
# These are technically specific to calibre phase
/MODULE.*COMPLETED/ { print; print ""; next; }
/MODULE/ { print; next }
/Calibre v/ { print; print ""; next }
/Rule file generated/   { print; next }
/OPS COMPLETE.*000\ OF/ { print; next }



########################################################################
# Phase-dependent checks (mostly)

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


########################################
# INNOVUS phase(s)
phase == "innovus" && /ERROR/ { print; next }
phase == "innovus" && /^Cadence|^Version/  { print; next }
phase == "innovus" && /Sourcing|starts at/ { print; next }



