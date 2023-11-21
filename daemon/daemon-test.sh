#!/bin/bash
set -e # exit if something fails

HELP='
# ------------------------------------------------------------------------
# 1. How to launch a docker session from kiwi
# in a separate window with a pink background:

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

# ------------------------------------------------------------------------
# 2. How to run the daemon test from inside docker

# --- in docker now ---
source /aha/bin/activate
(cd garnet; git fetch origin; git checkout origin/refactor)
# garnet/daemon/daemon-test.sh |& tee dtest.log | less -r
garnet/daemon/daemon-test.sh >& dtest.log &
tail -f dtest.log | less -r
tail -f dtest.log

# see CUT`N`PASTE region below

# ------------------------------------------------------------------------
# 3. How to transfer files from kiwi to docker etc.

# --- other useful things ---
docker cp /usr/bin/vim.tiny $container:/usr/bin
alias vim=vim.tiny
alias j=jobs
alias h='history|tail'

GARNET=/nobackup/steveri/github/garnet
f=garnet.py
docker cp $GARNET/$f $container:/aha/garnet/$f
f=daemon/daemon.py
f=daemon/daemon-test.sh
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

# Duplicate this table with and without daemon

# FLAGS1
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

# Using 'aha pnr' instead maybe?
# flags2=`get_flags2 $app`; echo flags2=$flags2 | fold -sw 120

aha garnet --daemon kill

app=apps/pointwise
apps='
    apps/pointwise
    tests/ushift
    tests/arith
    tests/absolute
    tests/scomp
    tests/ucomp
    tests/uminmax
    tests/rom
    tests/conv_1_2
    tests/conv_2_1
'
# Don't rightly know how to do conv5 yet...
#     conv5_1 
#         resnet_tests = ["conv5_1"]
#     for test in glb_tests:
#         t0, t1, t2 = test_dense_app(test, width, height, env_parameters=str(args.env_parameters))
#     for test in resnet_tests:
#         t0, t1, t2 = test_dense_app("apps/resnet_output_stationary", width, height, layer=test, env_parameters=str(args.env_parameters))

# GARNET BUILD & LAUNCH DAEMON
echo "--- BEGIN BUILD & LAUNCH DAEMON"
t_start=`date +%s`
aha garnet $flags1 --daemon launch |& sed 's/^/DAEMON: /' | tee garnet.log &
aha garnet --daemon wait
t_garnet=$(( `date +%s` - $t_start ))
echo "Initial garnet build took $t_garnet seconds"

(
    printf "%s\n" "Step                 Total(d)    Compile(d)   Map(d)     Test(d) " ;
    printf "%s\n" "------------------- ----------   ----------  --------   ---------" ;
    printf "%-19s %4s %-6s\n" garnet $t_garnet "($t_garnet)" ;
) >& tmp.stats

for app in $apps; do
    ap=`basename $app`; echo $ap
    echo "--- BEGIN TEST $ap"

# Using 'aha pnr' instead maybe?
# flags2=`get_flags2 $app`
# echo flags2=$flags2 | fold -sw 120

# bookmark NEW STUFF
(
    set -x
    cd /aha/Halide-to-Hardware/apps/hardware_benchmarks/$app
    make clean 
    cd /aha
)

echo "--- BEGIN MAP $ap"
# MAP ("COMPILE")
t_start=`date +%s`
aha map ${app} --chain |& tee map.log
t_map=$(( `date +%s` - $t_start ))
echo "'$ap' map took $t_map seconds"

set -x
echo "--- BEGIN PNR $ap, no daemon"
# PNR ("MAP"), no daemon
t_start=`date +%s`
# aha garnet $flags2 |& tee pnr_no_daemon.log
aha pnr $app --width 28 --height 16 |& tee pnr_no_daemon.log
t_pnr_no_daemon=$(( `date +%s` - $t_start ))
echo "No-daemon '$ap' pnr took $t_pnr_no_daemon seconds"

echo "--- BEGIN PNR $ap, using daemon"
# PNR ("MAP"), using daemon
t_start=`date +%s`
# aha garnet $flags2 --daemon use |& tee pnr_daemon.log
aha pnr $app --width 28 --height 16 --daemon use |& tee pnr_daemon.log
aha garnet --daemon wait
t_pnr_daemon=$(( `date +%s` - $t_start ))
echo "'$ap' w/daemon pnr took $t_pnr_daemon seconds"
set +x

# # TODO probably don't need this now that we are using "aha pnr"
# # PARSE DESIGN_META (create design_meta.json for test)
# echo "--- BEGIN DESIGN PARSE $ap, using daemon"
# app_dir=/aha/Halide-to-Hardware/apps/hardware_benchmarks/${app}
# dmj=${app_dir}/bin/design_meta.json
# test -e $dmj && echo found json file || echo "NO JSON FILE (yet)"
# cd $app_dir
#   pdm=/aha/Halide-to-Hardware/apps/hardware_benchmarks/hw_support/parse_design_meta.py
#   python $pdm bin/design_meta_halide.json --top bin/design_top.json --place bin/design.place
# cd /aha
# test -e $dmj && echo found json file || echo "NO JSON FILE (yet)"

# POINTWISE TEST
t_start=`date +%s`
if ! which vcs; then
  . /cad/modules/tcl/init/bash
    module load base; module load vcs
fi
aha test apps/pointwise |& tee test.log
t_test=$(( `date +%s` - $t_start ))
echo "'$ap' test took $t_test seconds"

echo "--- BEGIN SUMMARY 1 $ap"
# SUMMARY 1
# 
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

echo "--- BEGIN SUMMARY 2 $ap"
# SUMMARY 2
# 
# Step                 Total(d)    Compile(d)   Map(d)     Test(d) 
# ------------------- ----------   ----------  --------   ---------
# garnet               640 (640) 
# apps/pointwise       204 (137)    60 (60)    135 (68)      9 (9)   

# printf "%s\n" "Step                 Total(d)    Compile(d)   Map(d)     Test(d) " ;\
# printf "%s\n" "------------------- ----------   ----------  --------   ---------" ;\
# printf "%-19s %4s %-6s\n" garnet $t_garnet "($t_garnet)" ;\
# printf "%-19s %4s %-6s %4s %-6s %4s %-6s %4s %-6s\n" \
#        $app \
#        $t_total_no_daemon "($t_total_daemon)" \
#        $t_map             "($t_map)" \
#        $t_pnr_no_daemon   "($t_pnr_daemon)" \
#        $t_test            "($t_test)"

printf "%-19s %4s %-6s %4s %-6s %4s %-6s %4s %-6s\n" \
       $app \
       $t_total_no_daemon "($t_total_daemon)" \
       $t_map             "($t_map)" \
       $t_pnr_no_daemon   "($t_pnr_daemon)" \
       $t_test            "($t_test)" \
       >> tmp.stats
cat tmp.stats

done
