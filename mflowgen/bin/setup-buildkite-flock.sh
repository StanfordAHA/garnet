##############################################################################
# Initiate a LOCK region where no other script can run until lock is released,
# either by script EXIT (see trap below) or by explicitly doing 'flock -u 9'
# 
# Script will wait up to an hour before giving up.
# 
# EXAMPLE
#    # Initiate a lock
#    source $0
#
#    # Do something that should only be done one at a time, e.g. might not
#    # want two processes trying to clone the same repo at the same time.
#    git clone REPO
#
#    # Release the lock when done
#    flock -u 9

LOCK=/tmp/setup-buildkite.lock

# E.g. "05/11 17:34 41033 your name here"
function flockmsg  {
    pnum=$$; msg="$1";
    echo `date +'%m/%d %H:%M'` $pnum "$msg"; 
}

function flockwait {
    msg="WARNING waited $1 minutes, could not get lock from `cat $LOCK`"
    flock -w 600 9 || flockmsg "$msg"
}

date; flockmsg "I am process $$ and I want lock '$LOCK'"

exec 9>> $LOCK

if ! flock -n 9; then
    # echo `flockdate` $$ "Waiting for process `cat $LOCK` to release the lock..."
    flockmsg "Waiting for process `cat $LOCK` to release the lock..."
    flockwait 10
    flockwait 20
    flockwait 30
    flockwait 40
    flockwait 50
    if ! flock -w 600 9; then
        flockmsg "ERROR waited 60 minutes, could not get lock from `cat $LOCK`"
        echo "Might want to delete the lock file '$LOCK'"
        return 13 || exit 13
    fi
fi
date; flockmsg "Lock acquired! Prev owner was " `cat $LOCK`
echo $$ > $LOCK; # Record who has the lock (i.e. me)

# Failsafe: Release lock on exit (if not before).  Note, because this
# script is sourced, this trap won't kick in until calling process dies.
trap "flock -u 9" EXIT

