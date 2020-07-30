# Filter for lvs buildkite log

# Don't start filter until step begins

BEGIN { PRINTALL=1 }
/Checking preconditions for .*mentor-calibre-lvs/ { PRINTALL=0 }
# PRINTALL { print "PA " $0; next }
PRINTALL { print "PA " $0; next }

# heartbeat i guess, see what happens
BEGIN { HEARTBEAT=1 }
{
    date = strftime("%H:%M")
    nbeats++
    if (nbeats >= HEARTBEAT) { 
        if (HEARTBEAT==1)   printf("HB%05d %s\n", HEARTBEAT, date);
        if (HEARTBEAT>1000) printf("HB%05d %s\n", HEARTBEAT, date);
        printf("HB%05d %s\n", HEARTBEAT, $0);
        HEARTBEAT = HEARTBEAT * 2; 
        next; 
    }
}    

# Show max 20 warnings
{
    IGNORECASE = 1
    if ($0 ~ /warn/) {
        nwarns++; if (nwarns < 20) {
            # print "FOO " $0
            print "WA" $0
            next
        }
    }
    IGNORECASE = 0
}

# Show ALL warning/error/pass/fail lines
{
    IGNORECASE = 1
    if      ($0 ~ /error/) { print "WE " $0; next }
    else if ($0 ~ /pass/)  { 
        if ($0 ~ /YPASS/) { next } ; # Ignore false positives :(
        print "WE " $0; next 
    }
    else if ($0 ~ /fail/)  { print "WE " $0; next }
    IGNORECASE = 0
}

# Show timedesign summary
BEGIN { TDSUMMARY=0 }
/Profile/ { TDSUMMARY=0 }
TDSUMMARY==1 { print; next }
/timeDesign Summary/ {
    TDSUMMARY=1
    print "------------------------------------------------------------"
    print $0
    next
}
# ------------------------------------------------------------
#           timeDesign Summary                             
# ------------------------------------------------------------
# 
# Hold  views included:
#  analysis_default
# 
# +--------------------+---------+---------+---------+---------+
# |     Hold mode      |   all   | reg2reg |reg2cgate| default |
# +--------------------+---------+---------+---------+---------+
# |           WNS (ns):| -0.612  | -0.612  | -0.024  |  0.611  |
# |           TNS (ns):| -2.282  | -2.040  | -0.242  |  0.000  |
# |    Violating Paths:|   93    |   71    |   22    |    0    |
# |          All Paths:|  81113  |  76601  |  3846   |   756   |
# +--------------------+---------+---------+---------+---------+
# |analysis_default    | -0.612  | -0.612  | -0.024  |  0.611  |
# |                    | -2.282  | -2.040  | -0.242  |  0.000  |
# |                    |   93    |   71    |   22    |    0    |
# |                    |  81113  |  76601  |  3846   |   756   |
# +--------------------+---------+---------+---------+---------+
# 
# Density: 1.179%
#        (376.862% with Fillers)
# ------------------------------------------------------------
# ** Profile ** Report data :  cpu=0:02:44, mem=12376.0M

# Show end matter
/LVS completed/    { PRINTALL=1 }
