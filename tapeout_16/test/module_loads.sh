# must be SOURCED not executed :(

# For "module load" requirements see README, alex .cshrc
# FIXME consider a "requirements.txt" for module load's

# echo HOME=$HOME    # HOME=/var/lib/buildkite-agent
# echo USER=$USER    # USER=buildkite-agent

# To forestall warning : '/home/steveri/.modules' not found
# +(0):WARN:0: Directory '/var/lib/buildkite-agent/.modules' not found
# 
# echo HOME=$HOME; ls -l $HOME/.modules
test -f $HOME/.modules && rm    $HOME/.modules # fix your wagon!
test -d $HOME/.modules || mkdir $HOME/.modules

set +x
source /cad/modules/tcl/init/bash

# module load base
# module load genesis2
# module load incisive/15.20.022
# module load lc
# module load syn/latest
modules="base genesis2 incisive/15.20.022 lc syn/latest"
echo - loading modules: $modules
# for m in base genesis2 incisive/15.20.022 lc syn/latest; do
for m in $modules; do
  echo -- module load $m; module load $m
done

# Note alternative for genesis2 load is keyi's possibly-more-reliable
# "pip install genesis2"



##############################################################################
# Special consideration for weird innovus v. genus dependence...
echo "
  # NOTE 'module load genus' loads innovus v17 as a side effect.
  # So to get the correct innovus v19, 
  # 'module load innovus/19' must happen *after* 'module load genus'.
"
# Filter turns "/usr/bin/which: no innovus in (/cad/synopsys/syn/P-2019.0..."
# into         "/usr/bin/which: no innovus"

echo ""; echo "Before:"
/usr/bin/which innovus |& sed 's/ in .*//'
/usr/bin/which genus   |& sed 's/ in .*//'

echo ""; echo "Load:"
echo -- module load genus;      module load genus
echo -- module load innovus/19; module load innovus/19.10.000

echo ""; echo "After:"
/usr/bin/which innovus |& sed 's/ in .*//'
/usr/bin/which genus   |& sed 's/ in .*//'


# Verify final versions. Should be
#   /cad/cadence/GENUS17.21.000.lnx86/bin/genus
#   /cad/cadence/INNOVUS19.10.000.lnx86/bin/innovus

version_found=`/usr/bin/which innovus`
version_wanted="/cad/cadence/INNOVUS19.10.000.lnx86/bin/innovus"
if [ $version_found != $version_wanted ] ; then
    echo ""
    echo "ERROR innovus version changed"
    echo "- found  '$version_found'"
    echo "- wanted '$version_wanted'"
    exit 13
fi
version_found=`/usr/bin/which genus`
version_wanted="/cad/cadence/GENUS17.21.000.lnx86/bin/genus"
if [ $version_found != $version_wanted ] ; then
    echo ""
    echo "ERROR genus version changed"
    echo "- found  '$version_found'"
    echo "- wanted '$version_wanted'"
    exit 13
fi
