#!/bin/bash
set -eu ; # exit immediately on failure

# Generate the next two qrc checks to run simultaneously, e.g.
#   steps:
#   - label:   run1a
#     command: '.buildkite/bin/prh.sh /build/prh3555/run1 else fail2'
#   - label:   run2
#     command: '.buildkite/bin/prh.sh /build/prh3555/run2 else fail1'
# 
# "prh.sh /build/prh3555/run2 else fail1" should do something like this:
#    - build new dir "/build/prh355/run2" and run qrc
#    - if prc succeeds, rename "/build/prh355/run2" => "/build/prh355/run2-pass
#    - if prc fails, rename "/build/prh355/run2" => "/build/prh355/run2-fail1"
# 
# Final directory structure should look something like this:
# 
#   % ls -1 /build/prh3555/
#   run0-pass
#   run1-fail1
#   run1-fail2
#   run1-pass
#   ...
# 
#  ------------------------------------------------------------------
#  Call this script with something like
# 
#    env:
#        BUILDPIPE : ".buildkite/prh-twostep.sh /build/prh3555"
# 
#    steps:
#      # Each upload inserts the next two steps into the pipeline
#      # Steps run in parallel, does not continue until both are done.
#      # Repeat five times for ten total tests including retries
#      - command: '$$BUILDPIPE | buildkite-agent pipeline upload'
#      - wait: { continue_on_failure: true }
# 
#  ------------------------------------------------------------------

# function build_step generates e.g. one of
#   build_step prh.sh $rundir run$i else fail1 ; # first try
#   build_step prh.sh $rundir run$i else fail2 ; # failed once; retry

function build_step {
    # E.g. "build_step
    cmd=$1;      # should be 'prh.sh'
    rundir=$2;   # e.g. '/build/prh3555/run0'
    label=$3;    # e.g. 'run0'
    failname=$4; # e.g. 'fail1' or 'fail2'

    # e.g. 'run0' or 'run0a'
    [ "$failname" == "fail2" ] && label=${label}a ; # e.g. 'run0a' for retry #1

    cat<<EOF

    - label:   $label
      command: '.buildkite/bin/prh.sh $rundir else $failname'
EOF
}

echo "steps:"
njobs=0; 

# Grab next two run dirs for the jobs
for i in 0 1 2 3 4 5 6 7 8 9; do
    rundir=$1/run$i ; # e.g. '/build/prh3555/run0'
    test -e $rundir         && echo "ooh something borked" && continue
    test -e ${rundir}-pass  && continue; # run passed
    test -e ${rundir}-fail2 && continue; # run reached max retries

    # If we get this far, ready to run the next test in subdir run$i
    if test -e ${rundir}-fail1; then
        build_step prh.sh $rundir run$i fail2 ; # failed once; retry
    else
        build_step prh.sh $rundir run$i fail1 ; # first try
    fi

    # Launch a maximum of two jobs to run in parallel    
    njobs=$((njobs+1))
    if [ $njobs -ge 2 ]; then break; else continue; fi
done
