#!/bin/bash

set -eu ; # exit immediately on failure

cat <<EOF>/dev/null
    Want final directory structure to look something like:


    /build/prh3555/
      run0-pass
      run1-fail1
      run1-fail2
      run1-pass
      ...

    ------------------------------------------------------------------
    Call this script with something like
      prh-pipeline.sh "/build/prh3555"

      env:
          buildpipe ".buildkite/prh-pipeline.sh /build/prh3555"

      steps:

        # Each upload inserts the next two steps into the pipeline
        # Steps run in parallel, does not continue until both are done.
        # Repeat five times for ten total tests including retries

        - command: '$$buildpipe | buildkite-agent pipeline upload'
          label: "gensteps"
        - wait: { continue_on_failure: true }

        - command: '$$buildpipe | buildkite-agent pipeline upload'
          label: "gensteps"
        - wait: { continue_on_failure: true }

        - command: '$$buildpipe | buildkite-agent pipeline upload'
          label: "gensteps"
        - wait: { continue_on_failure: true }

        - command: '$$buildpipe | buildkite-agent pipeline upload'
          label: "gensteps"
        - wait: { continue_on_failure: true }

        - command: '$$buildpipe | buildkite-agent pipeline upload'
          label: "gensteps"

    ------------------------------------------------------------------
    prh-pipeline.sh generates the next two pipe steps, something like
        steps:
          - command: qrc.sh /build/prh3555/run0 fail2
            label: run0a
          - command: qrc.sh /build/prh3555/run1 fail1
            label: run1

    ...by doing something like

    
      njobs=0
      for i in 0 1 2 3 4 5 6 7 8 9; do
          rundir=\$1/run\$i ; # e.g. '/build/prh3555/run0'
          test -e \$rundir && echo "ooh something borked" && continue
          test -e \${rundir}-pass  && continue; # run passed
          test -e \${rundir}-fail2 && continue; # run reached max retries
          if test -e \${rundir}-fail1; then
              build_step prh.sh \$rundir run\$i fail2 ; # failed once; retry
          else
              build_step prh.sh \$rundir run\$i fail1 ; # first try
          fi
          njobs++
          if (\$njobs==2); then break; else continue; fi
      done
      echo " - wait:     { continue_on_failure: true }"
      exit

    prh.sh /build/prh3555/run0 does this:
      build and run in dir rundir=/build/prh3555/run0
      if PASS then mv \$rundir \${rundir}-pass
      else for i in 1 2 3 4 5 6 7 8 9; do
        failname=\${rundir}-fail\$i
        if ! -e \$failname; then mv \$rundir \$failname; break; fi
      fi

EOF


# test 1 GOOD
# date=`date +%H%M`
# cat <<EOF
# steps:
#   - label: $date fail
#     command: 'echo fail 10; sleep 10; exit 13'
#   - label: $date pass
#     command: 'echo pass 20; sleep 20; exit 0'
# EOF
# exit

# E.g.
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

    label:   $label
    command: '.buildkite/bin/prh.sh $rundir else $failname'
EOF
}

#     touch ${rundir}-pass
#     touch ${rundir}-$failname
#     command: 'echo .buildkite/bin/prh.sh $rundir else $failname'


#     label:   $label



echo "steps:"

njobs=0
for i in 0 1 2 3 4 5 6 7 8 9; do
    rundir=$1/run$i ; # e.g. '/build/prh3555/run0'
    test -e $rundir         && echo "ooh something borked" && continue
    test -e ${rundir}-pass  && continue; # run passed
    test -e ${rundir}-fail2 && continue; # run reached max retries
    if test -e ${rundir}-fail1; then
        build_step prh.sh $rundir run$i fail2 ; # failed once; retry
    else
        build_step prh.sh $rundir run$i fail1 ; # first try
    fi
    njobs=$((njobs+1))
    if [ $njobs -ge 2 ]; then break; else continue; fi
done

# Caller does this
# echo " - wait:     { continue_on_failure: true }"

exit

# TEST:

mkdir -p /tmp/deleteme
prh-twostep.sh /tmp/deleteme




# # E.g.
# #   build_step prh.sh $rundir run$i fail1 ; # first try
# #   build_step prh.sh $rundir run$i fail2 ; # failed once; retry
# 
# function build_step {
#     # E.g. "build_step
#     cmd=$1;      # should be 'prh.sh'
#     rundir=$2;   # e.g. '/build/prh3555/run0'
#     label=$3;    # e.g. 'run0'
#     failname=$4; # e.g. 'fail1' or 'fail2'
# 
#     [ "$failname" == "fail2" ] && label=${label}a ; # e.g. 'run0a' for retry #1
# 
#     label: 'run0' or 'run0a'
#     command: "prh.sh $rundir"; # failed once; retry
# }

