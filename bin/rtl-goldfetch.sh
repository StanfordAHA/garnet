#!/bin/bash

cmd=$0; HELP="
DESCRIPTION:
  Tells how to update RTL gold model.

  Assumes docker container on 'hostname' recently ran
  and copied design.v file to e.g. /tmp/amber-4x2.v

USAGE:
  $cmd <hostname> amber      # Tell how to update amber model
  $cmd <hostname> onyx       # Tell how to update onyx model

EXAMPLE
  % $cmd r7arm-aha onyx

  HOW TO UPDATE GOLD MODEL when/if diffs are benign:

    scp r7arm-aha:/tmp/design.v /tmp/onyx-4x2
    gunzip -c \$GARNET_REPO/bin/ref/onyx-4x2.v.gz > /tmp/gold.v
    \$GARNET_REPO/bin/rtl-goldcompare.sh /tmp/gold.v /tmp/onyx-4x2.v
    gzip /tmp/onyx-4x2.v; mv /tmp/onyx.v.gz \$GARNET_REPO/bin/ref/
"
[ "$1" == "--help" ] && echo "$HELP" && exit
[ "$1" == "" ] && echo "$HELP" && exit


hostname=$1 # Name of host where docker container ran
soc=$2    # E.g. "amber" or "onyx"

cat <<EOF
HOW TO UPDATE GOLD MODEL when/if diffs are benign:

  scp ${hostname}:/tmp/design.v /tmp/${soc}-4x2
  gunzip -c \$GARNET_REPO/bin/ref/${soc}-4x2.v.gz > /tmp/gold.v
  \$GARNET_REPO/bin/rtl-goldcompare.sh /tmp/gold.v /tmp/${soc}-4x2.v
  gzip /tmp/${soc}-4x2.v; mv /tmp/${soc}.v.gz \$GARNET_REPO/bin/ref/";
EOF
