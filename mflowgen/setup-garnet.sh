source /cad/modules/tcl/init/sh

module load base/1.0
[ "$WHICH_SOC" == "amber" ] && module load genesis2
module load xcelium/19.03.003
module load icadv/12.30.712
module load incisive/15.20.022
module load vcs/Q-2020.03-SP2
module load verdi/Q-2020.03-SP2-3
module load genus/19.10.000
module load innovus/19.10.000
module load lc/M-2017.06-SP3
module load syn/P-2019.03

########################################################################
# Loading calibre/2019.1 results in loading mentor versions of binaries
# e.g.
#   /cad/mentor/2019.1/aoi_cal_2019.1_18.11/bin/tclsh and python3
#
# These binaries *do not work* on ubuntu systems. Worse, they usurp
# the previously existing/working binaries in your path so that if
# you try to run e.g. "python3" or "tclsh" from the command line you
# just get the cryptic error "Invalid operating system environment".
#
# Because tclsh is thusly poisoned, the "module load" commands stop
# working, among whatever other bad things might happen.
#
# My fix is to just skip this load if the OS is Ubuntu...
#
# 03-2023 update: I just checked, and yes calibre/2021 has the same problem.

tmp=`lsb_release -i | awk '{print $NF}'`
if [ "$tmp" == "Ubuntu" ]; then
    echo "Skipping calibre load because its binaries don't work under Ubuntu"
else
    # Amber uses 2019 version, all others use 2021
    [ "$WHICH_SOC" == "amber" ] && module load calibre/2019.1
    [ "$WHICH_SOC" == "amber" ] || module load calibre/2021.2_18
fi

module load prime/latest
module load ext/latest

##############################################################################
# OA_HOME weirdness -- 08/2024 moved this here verbatim from setup-buildkite.sh
# OA_HOME *** WILL DRIVE ME MAD!!! ***
echo "--- UNSET OA_HOME"
echo ""
echo "buildkite (but not arm7 (???)) errs if OA_HOME is set"
echo "BEFORE: OA_HOME=$OA_HOME"
echo "unset OA_HOME"
unset OA_HOME
echo "AFTER:  OA_HOME=$OA_HOME"
echo ""


# 08/2024 Joe upgraded system to redhat-compatible "rocky" i.e.
# 'cat /etc/redhat-release' yields the string "Rocky Linux release 8.10 (Green Obsidian)"
# calibre binaries die because they invoke a script 'calibre_host_info' that expects
# 'cat /etc/redhat-release' to test positive for `egrep -i 'centos|red *hat|redhat|suse|sles'`,
# so 'cgra_info' sets 'OS_VENDOR=unknown' and then the follow-on script 'calibre_vco'
# errs out with a message like "Invalid operating system environment"

# We can prevent this (maybe?) by setting an environment variable
# 'export USE_CALIBRE_VCO=aoi' that shortcuts the OS check.

test -e /etc/os-release && source /etc/os-release  # Sets os-related vars including ID
[ "$ID" == "rocky" ] && export USE_CALIBRE_VCO=aoi

# 08/2024 Joe upgraded some of the machines from rhel 7 to rocky 8
# and oh boy did that mess things up

# Let's try a thing maybe
test -e /etc/os-release && source /etc/os-release  # Sets os-related vars including ID
if [ "$ID" == "rocky" ]; then
    echo "reset OA_HOME" etc.
    unset OA_UNSUPPORTED_PLAT
    export OA_HOME=/cad/cadence/ICADVM20.10.330/oa_v22.60.090
    echo "NOW:  OA_HOME=$OA_HOME"
    echo "NOW:  OA_UNSUPPORTED_PLAT is unset"
    echo "NOW:  USE_CALIBRE_VCO=$USE_CALIBRE_VCO"
fi
