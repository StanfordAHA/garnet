#!/bin/bash
set -e # exit if something fails

HELP='
# ------------------------------------------------------------------------
# 1. Launch docker session from kiwi in separate window w a pink background

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
docker kill $container
docker-launch $image $container

# ------------------------------------------------------------------------
# 2. How to run the daemon test from inside docker

# --- in docker now ---
source /aha/bin/activate
# (cd garnet; git fetch origin; git checkout origin/refactor)
garnet/daemon/daemon-test.sh >& dtest.log &
tail -f dtest.log

# ------------------------------------------------------------------------
# 3. How to transfer files from kiwi to docker etc.

# --- transfer files
GARNET=/nobackup/steveri/github/garnet
f=garnet.py; docker cp $GARNET/$f $container:/aha/garnet/$f
f=daemon/daemon.py; docker cp $GARNET/$f $container:/aha/garnet/$f
f=daemon/daemon-test.sh; docker cp $GARNET/$f $container:/aha/garnet/$f

# --- other useful things ---
docker cp /usr/bin/vim.tiny $container:/usr/bin
alias vim=vim.tiny
alias j=jobs
alias h="history|tail"

'
if [ "$1" == "--help" ]; then echo "$HELP"; exit; fi

echo "--- BEGIN DAEMON_TEST.SH"

##############################################################################
# Garnet build 4610:
# https://buildkite.com/stanford-aha/garnet/builds/4610
# 
# step                     total    compile      map      test
# -------------------  ---------  ---------  -------  --------
# garnet                906.979
# apps/pointwise_glb    292.944     80.002   178.783   34.1585
# tests/ushift_glb      277.462     63.6381  178.721   35.103
# ...
# 
# Goal: duplicate the above table with and without daemon

# FLAGS1
flags1="--width  4 --height  2 --verilog --use_sim_sram --rv --sparse-cgra --sparse-cgra-combined"
flags1="--width 28 --height 16 --verilog --use_sim_sram --rv --sparse-cgra --sparse-cgra-combined"
echo flags1=$flags1 | fold -sw 120

# Using 'aha pnr' instead maybe?
# # FLAGS2
# function get_flags2 {
#     args_app=$1
#     ext=.pgm
#     args_app_name=`expr $args_app : '.*/\(.*\)'`
#     app_dir=/aha/Halide-to-Hardware/apps/hardware_benchmarks/${args_app}
#     test -e $app_dir/bin/input.pgm && ext=.pgm
#     flags2="--no-pd --interconnect-only"
#     flags2+=" --input-app ${app_dir}/bin/design_top.json"
#     flags2+=" --input-file ${app_dir}/bin/input${ext}"
#     flags2+=" --output-file ${app_dir}/bin/${args_app_name}.bs"
#     flags2+=" --gold-file ${app_dir}/bin/gold${ext}"
#     flags2+=" --input-broadcast-branch-factor 2"
#     flags2+=" --input-broadcast-max-leaves 16"
#     flags2+=" --rv --sparse-cgra --sparse-cgra-combined --pipeline-pnr"
#     flags2+=" --width 28 --height 16"
#     # echo flags2=$flags2 | fold -sw 120
#     echo $flags2
# }
# flags2=`get_flags2 apps/pointwise`
# echo flags2=$flags2 | fold -sw 120

##############################################################################
# BEGIN BUILD & RUN

# Kill existing daemon if one exists
aha garnet --daemon kill

apps='
    apps/pointwise
    apps/pointwise
    tests/ushift
    tests/arith
    conv1
    conv3_1
    tests/absolute
    tests/scomp
    tests/ucomp
    tests/uminmax
    tests/rom
    tests/conv_1_2
    tests/conv_2_1
'

echo "--- (daemon-test.sh) GARNET VERILOG BUILD"
t_start=`date +%s`
aha garnet $flags1 |& tee garnet.log
t_garnet=$(( `date +%s` - $t_start ))
echo "Initial garnet build took $t_garnet seconds"
(
    printf "%s\n" "Step                 Total(d)    Compile(d)   Map(d)     Test(d) " ;
    printf "%s\n" "------------------- ----------   ----------  --------   ---------" ;
    printf "%-19s %4s %-6s\n" garnet $t_garnet "($t_garnet)" ;
) >& tmp.stats

DAEMON_LAUNCHED=
for app in $apps; do
    ap=`basename $app`; echo $ap
    echo "--- (daemon-test.sh) $ap"
    layer=""
    if expr $app : conv > /dev/null; then 
        layer="--layer $app"
        app=apps/resnet_output_stationary
    fi

# Using 'aha pnr' instead maybe?
# flags2=`get_flags2 $app`; echo flags2=$flags2 | fold -sw 120

app_path=/aha/Halide-to-Hardware/apps/hardware_benchmarks/$app
cd $app_path; make clean; cd /aha


echo "--- (daemon-test.sh) MAP $ap"
# MAP ("COMPILE")
t_start=`date +%s`
aha map $app --chain $layer |& tee map.log
t_map=$(( `date +%s` - $t_start ))
echo "'$ap' map took $t_map seconds"


echo "--- (daemon-test.sh) PNR $ap, no daemon"
# PNR ("MAP"), no daemon
t_start=`date +%s`
# aha garnet $flags2 |& tee pnr_no_daemon.log
aha pnr $app --width 28 --height 16 $layer |& tee pnr_no_daemon.log
t_pnr_no_daemon=$(( `date +%s` - $t_start ))
echo "No-daemon '$ap' pnr took $t_pnr_no_daemon seconds"

# Using 'aha pnr' instead of flags2 maybe?
# flags2=`get_flags2 $app`; echo flags2=$flags2 | fold -sw 120

echo "--- (daemon-test.sh) PNR $ap, using daemon"
# PNR ("MAP"), using daemon
# First time through, launch the daemon; aftwerwards *use* the daemon
t_start=`date +%s`; nobuf='stdbuf -oL -eL'
if ! [ "$DAEMON_LAUNCHED" ]; then
    echo '--- daemon-test.sh LAUNCHING A NEW DAEMON maybe'
    echo   aha pnr $app --width 28 --height 16 $layer --daemon auto
    $nobuf aha pnr $app --width 28 --height 16 $layer --daemon auto \
        |& $nobuf sed 's/^/DAEMON: /' \
        |  $nobuf tee pnr_launch.log &

    # Wait (up to) a couple minutes for daemon to launch
    echo '--- daemon-test.sh WAITING FOR NEW DAEMON maybe'
    i=120; while test $((i--)) -gt 0; do
             echo -n .; grep LAUNCHING pnr_launch.log && break
             sleep 1
          done
    if ! grep LAUNCHING pnr_launch.log; then
        echo 'ooh somethings ripped'; exit 13
    fi
    DAEMON_LAUNCHED=True
else
    echo '--- USE EXISTING DAEMON maybe'
    echo   aha pnr $app --width 28 --height 16 $layer --daemon auto
    $nobuf aha pnr $app --width 28 --height 16 $layer --daemon auto \
        |& $nobuf tee pnr_use.log
fi

aha garnet --daemon wait  # Note, this dies if daemon not launched yet
t_pnr_daemon=$(( `date +%s` - $t_start ))
echo "'$ap' w/daemon pnr took $t_pnr_daemon seconds"

# TODO probably don't need this now that we are using "aha pnr"
# PARSE DESIGN_META (create design_meta.json for test)
# See far below for details

# TEST
t_start=`date +%s`
if ! which vcs; then
  . /cad/modules/tcl/init/bash
    module load base; module load vcs
fi
aha test $app |& tee test.log
t_test=$(( `date +%s` - $t_start ))
echo "'$ap' test took $t_test seconds"

# ========================================================================
echo "--- (daemon-test.sh) SUMMARY 1 $ap"

# Initial garnet build                   640 seconds
# ---------------------------------  -----------
# pointwise 'compile' (map)               60 seconds
# pointwise 'compile' (pnr) w/o daemon   135 seconds
# pointwise 'compile' (pnr) w/ daemon     68 seconds
# pointwise test                           9 seconds
# pointwise total, daemon                137 seconds
# pointwise total, no daemon             204 seconds

t_total_daemon=$((   $t_map + $t_pnr_daemon    + $t_test))
t_total_no_daemon=$(($t_map + $t_pnr_no_daemon + $t_test))

fmt="%-37s %4d seconds\n"
printf "$fmt" "Initial garnet build"  $t_garnet;\
printf "%s  %s\n" "---------------------------------" "-----------";\
printf "$fmt" "$ap 'compile' (map)"  $t_map;\
printf "$fmt" "$ap 'compile' (pnr) w/o daemon"  $t_pnr_no_daemon;\
printf "$fmt" "$ap 'compile' (pnr) w/ daemon"  $t_pnr_daemon;\
printf "$fmt" "$ap test"  $t_test;\
printf "$fmt" "$ap total, daemon"  $t_total_daemon; \
printf "$fmt" "$ap total, no daemon"  $t_total_no_daemon

# ========================================================================
echo "--- (daemon-test.sh) SUMMARY 2 $ap (tmp.stats)"

# Step                 Total(d)    Compile(d)   Map(d)     Test(d) 
# ------------------- ----------   ----------  --------   ---------
# garnet               640 (640) 
# apps/pointwise       204 (137)    60 (60)    135 (68)      9 (9)   
# ...

printf "%-19s %4s %-6s %4s %-6s %4s %-6s %4s %-6s\n" \
       $ap \
       $t_total_no_daemon "($t_total_daemon)" \
       $t_map             "($t_map)" \
       $t_pnr_no_daemon   "($t_pnr_daemon)" \
       $t_test            "($t_test)" \
       >> tmp.stats
cat tmp.stats

done

##############################################################################
# # TODO probably don't need this now that we are using "aha pnr"
# # PARSE DESIGN_META (create design_meta.json for test)
# echo "--- (daemon-test.sh) DESIGN PARSE $ap, using daemon"
# app_dir=/aha/Halide-to-Hardware/apps/hardware_benchmarks/${app}
# dmj=${app_dir}/bin/design_meta.json
# test -e $dmj && echo found json file || echo "NO JSON FILE (yet)"
# cd $app_dir
#   pdm=/aha/Halide-to-Hardware/apps/hardware_benchmarks/hw_support/parse_design_meta.py
#   python $pdm bin/design_meta_halide.json --top bin/design_top.json --place bin/design.place
# cd /aha
# test -e $dmj && echo found json file || echo "NO JSON FILE (yet)"
