##############################################################################
# LOCK so that no two script instances can run at the same time.
# In particular, do not want e.g. competing 'git clone' or
# 'pip install' ops trying to access the same directory etc.

echo "--- LOCK"
function flockdate { date +'%m/%d %H:%M'; }  # E.g. "05/11 17:34"
LOCK=/tmp/setup-buildkite.lock
exec 9>> $LOCK
date; echo `flockdate` $$ "I am process $$ and I want lock '$LOCK'"
if ! flock -n 9; then
    echo `flockdate` $$ "Waiting for process `cat $LOCK` to release the lock..."
    flock -w 600 9 || echo `flockdate` $$ "WARNING waited 10 minutes, could not get lock from `cat $LOCK`"
    flock -w 600 9 || echo `flockdate` $$ "WARNING waited 20 minutes, could not get lock from `cat $LOCK`"
    flock -w 600 9 || echo `flockdate` $$ "WARNING waited 30 minutes, could not get lock from `cat $LOCK`"
    flock -w 600 9 || echo `flockdate` $$ "WARNING waited 40 minutes, could not get lock from `cat $LOCK`"
    flock -w 600 9 || echo `flockdate` $$ "WARNING waited 50 minutes, could not get lock from `cat $LOCK`"
    if ! flock -w 600 9; then
        echo `flockdate` $$ "ERROR waited 60 minutes, could not get lock from `cat $LOCK`"
        return 13 || exit 13
    fi
fi
date; echo -n "Lock acquired! Prev owner was "; cat $LOCK
echo $$ > $LOCK; # Record who has the lock (i.e. me)

# Failsafe: Release lock on exit (if not before).  Note, because this
# script is sourced, this trap won't kick in until calling process dies.
trap "flock -u 9" EXIT

