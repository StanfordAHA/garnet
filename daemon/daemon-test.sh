#!/bin/bash

sq="'"
HELP='
# --- starting in kiwi ---
xterm -bg pink -fg black &

# --- now in pink xterm ---
function docker-launch {
  image=$1; container=$2; docker pull $image
  docker run -id --name $container --rm -v /cad:/cad $image bash
  docker exec -ti $container  /bin/bash
}
image=stanfordaha/garnet:latest
container=deleteme
docker-launch $image $container

# --- in docker now ---
source /aha/bin/activate
(cd garnet; git fetch origin; git checkout origin/refactor)
# garnet/daemon/daemon-test.sh |& tee dtest-log.txt | less
# see CUT'N'PASTE region below


# --- other useful things ---
docker cp /usr/bin/vim.tiny $container:/usr/bin
alias vim=vim.tiny

GARNET=/nobackup/steveri/github/garnet
f=garnet.py
f=daemon/daemon.py
docker cp $GARNET/$f $container:/aha/garnet/$f



dtest_kiwi=/nobackup/steveri/github/garnet/daemon/daemon-test.sh
dtest_docker=$container:/aha/garnet/daemon/daemon-test.sh
docker cp $dtest_kiwi $dtest_docker
'

# alias time='/usr/bin/time -f "\t%E real,\t%U user,\t%S sys"'

if [ "$1" == "--help" ]; then
    echo "$HELP"; exit
fi

set -x

app=apps/pointwise
dtop=/aha/Halide-to-Hardware/apps/hardware_benchmarks/${app}/bin/design_top.json

if test -f $dtop; then
    echo found app $app
else
    echo $app not ready yet, must map now
    aha map ${app} --chain |& tee map-$(basename app).log
fi

# CUT'N'PASTE REGION

# FLAGS1 / DAEMON LAUNCH
flags1="--width 28 --height 16 --verilog --use_sim_sram --rv --sparse-cgra --sparse-cgra-combined"
echo flags1=$flags1 | fold -sw 120

# DAEMON LAUNCH
export TIME="\t%E real,\t%U user,\t%S sys"
jobs  # <kill tail job maybe>
\time aha garnet $flags1 --daemon launch >& launch-log &
tail -f launch-log &
alias j=jobs
jobs  # <kill tail job maybe>

# DAEMON WAIT
function wait_for_deamon_ready {
    [ "$1" ] && timeout=$1 || timeout=10

    # unset DONE; while [ ! "$DONE" ]; do echo no done yet; DONE=4; done
    unset DONE; while [ ! "$DONE" ]; do
        size="--width 28 --height 16"
        python /aha/garnet/garnet.py --daemon status $size |& grep 'daemon_status: busy' || DONE=true
        echo "Daemon busy; waiting $timeout seconds..."
        sleep $timeout
    done
    python /aha/garnet/garnet.py --daemon status $size |& grep 'daemon_status: '
}
wait_for_deamon_ready 10

# MAP
aha map apps/pointwise --chain |& tee map.log
tail -f map.log &
jobs  # <kill tail job maybe>

# # PNR?
# aha pnr apps/pointwise --width 28 --height 16


# FLAGS2
ext=png; 
args_app="apps/pointwise"
args_app_name=`expr $args_app : '.*/\(.*\)'`
app_dir=/aha/Halide-to-Hardware/apps/hardware_benchmarks/${args_app}
flags2="--no-pd --interconnect-only"
flags2+=" --input-app ${app_dir}/bin/design_top.json"
flags2+=" --input-file ${app_dir}/bin/input${ext}"
flags2+=" --output-file ${app_dir}/bin/${args_app_name}.bs"
flags2+=" --gold-file ${app_dir}/bin/gold${ext}"
flags2+=" --input-broadcast-branch-factor 2"
flags2+=" --input-broadcast-max-leaves 16"
flags2+=" --rv --sparse-cgra --sparse-cgra-combined --pipeline-pnr"
flags2+=" --width 28 --height 16"
echo flags2=$flags2 | fold -sw 120

# DAEMON USE
tail -f launch-log &
export TIME="\t%E real,\t%U user,\t%S sys"
\time aha garnet $flags2 --daemon use |& tee use.log  # 0:03.18 real,   3.49 user,      3.85 sys

jobs  # <kill tail job maybe>

# PNR

# Unable to find /aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise/bin/design_meta.json
pwdir=/aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise
ls -l $pwdir/bin/design_meta.json  # cannot access
aha pnr apps/pointwise --width 28 --height 16 |& tee pnr.log
ls -l $pwdir/bin/design_meta.json  # exists


# TEST
which vcs
module load base; module load vcs
aha test apps/pointwise |& tee test.log
# APP0-pointwise passed



# NO-DAEMON, garnet master
(cd garnet; git fetch origin; git checkout origin/master)
\time aha garnet $flags1 |& tee flags1.log       # 10:47 real, 643 user, 13 sys
aha map ${app} --chain |& tee map-pointwise.log
\time aha garnet $flags2 |& tee flags2.log       #  2:20 real, 136 user,  8 sys




# Unable to find /aha/Halide-to-Hardware/apps/hardware_benchmarks/pointwise/bin/design_meta.json

ls /aha/Halide-to-Hardware/apps/hardware_benchmarks/pointwise/bin/


cp ./bin/map_result/pointwise/pointwise_to_metamapper.json ./bin/design_top.json
make: Leaving directory '/aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise'

ls /aha/Halide-to-Hardware/apps/hardware_benchmarks/apps/pointwise



























w=4; h=$((w/2))

# FLAGS1
flags1="--width $w --height $h --verilog --use_sim_sram --rv --sparse-cgra --sparse-cgra-combined"
echo flags1=$flags1 | fold -sw 120

# FLAGS2
args_app=apps/pointwise
args_app_name=`expr $args_app : '.*/\(.*\)'`
app_dir=/aha/Halide-to-Hardware/apps/hardware_benchmarks/${args_app}
ext=raw; [ -e ${app_dir}/bin/input.${ext} ] || ext=pgm

ia=${app_dir}/bin/design_top.json
if=${app_dir}/bin/input.${ext}
of=${app_dir}/bin/${args_app_name}.bs
gf=${app_dir}/bin/gold.${ext}
ls -l $ia $if $gf

w=4;h=2
flags2="--no-pd --interconnect-only --width $w --height $h"
flags2+=" --input-app $ia --input-file $if"
flags2+=" --output-file $of --gold-file $gf"
flags2+=" --input-broadcast-branch-factor 2"
flags2+=" --input-broadcast-max-leaves 16"
flags2+=" --rv --sparse-cgra --sparse-cgra-combined --pipeline-pnr"

echo flags2=$flags2 | fold -sw 120

export TIME="\t%E real,\t%U user,\t%S sys"

log=flags1-${w}x${h}.log
\time aha garnet $flags1 >& $log


log=flags2-${w}x${h}.log
\time aha garnet $flags2 >& $log &
