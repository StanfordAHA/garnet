#!/bin/bash

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
# garnet/daemon/daemon-test.sh |& tee dtest-log.txt | less -r
garnet/daemon/daemon-test.sh >& dtest-log.txt &
tail -f dtest-log.txt | less -r

# see CUT`N`PASTE region below

# ------------------------------------------------------------------------
# 3. How to transfer files from kiwi to docker etc.

# --- other useful things ---
docker cp /usr/bin/vim.tiny $container:/usr/bin
alias vim=vim.tiny

GARNET=/nobackup/steveri/github/garnet
f=garnet.py
docker cp $GARNET/$f $container:/aha/garnet/$f
f=daemon/daemon.py
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

# FLAGS2
function get_flags2 {
    args_app=$1
    ext=.pgm
    args_app_name=`expr $args_app : '.*/\(.*\)'`
    app_dir=/aha/Halide-to-Hardware/apps/hardware_benchmarks/${args_app}
    test -e $app_dir/bin/input.pgm && ext=.pgm
    flags2="--no-pd --interconnect-only"
    flags2+=" --input-app ${app_dir}/bin/design_top.json"
    flags2+=" --input-file ${app_dir}/bin/input${ext}"
    flags2+=" --output-file ${app_dir}/bin/${args_app_name}.bs"
    flags2+=" --gold-file ${app_dir}/bin/gold${ext}"
    flags2+=" --input-broadcast-branch-factor 2"
    flags2+=" --input-broadcast-max-leaves 16"
    flags2+=" --rv --sparse-cgra --sparse-cgra-combined --pipeline-pnr"
    flags2+=" --width 28 --height 16"
    # echo flags2=$flags2 | fold -sw 120
    echo $flags2
}
flags2=`get_flags2 apps/pointwise`
echo flags2=$flags2 | fold -sw 120

##############################################################################
# BEGIN BUILD & RUN
app=apps/pointwise
flags2=`get_flags2 $app`; echo flags2=$flags2 | fold -sw 120

aha garnet --daemon kill

# GARNET BUILD & LAUNCH DAEMON
t_start=`date +%s`
aha garnet $flags1 --daemon launch |& sed 's/^/DAEMON: /' | tee garnet.log &
aha garnet --daemon wait
t_garnet=$(( `date +%s` - $t_start ))
echo "Initial garnet build took $t_garnet seconds"

# MAP ("COMPILE")
t_start=`date +%s`
aha map ${app} --chain |& tee map.log
t_map=$(( `date +%s` - $t_start ))
echo "Pointwise map took $t_map seconds"

# PNR ("MAP"), using daemon
t_start=`date +%s`
aha garnet $flags2 --daemon use |& tee pnr_daemon.log
aha garnet --daemon wait
t_pnr_daemon=$(( `date +%s` - $t_start ))
echo "Pointwise w/daemon compile took $t_pnr_daemon seconds"

# PNR ("MAP"), no daemon
t_start=`date +%s`
aha garnet $flags2 |& tee pnr_no_daemon.log
t_pnr_no_daemon=$(( `date +%s` - $t_start ))
echo "No-daemon pointwise compile took $t_pnr_no_daemon seconds"

# PARSE DESIGN_META (create design_meta.json for test)
app_dir=/aha/Halide-to-Hardware/apps/hardware_benchmarks/${app}
dmj=${app_dir}/bin/design_meta.json
test -e $dmj && echo found json file || echo "NO JSON FILE (yet)"
cd $app_dir
  pdm=/aha/Halide-to-Hardware/apps/hardware_benchmarks/hw_support/parse_design_meta.py
  python $pdm bin/design_meta_halide.json --top bin/design_top.json --place bin/design.place
cd /aha
test -e $dmj && echo found json file || echo "NO JSON FILE (yet)"

# POINTWISE TEST
t_start=`date +%s`
if ! which vcs; then
  . /cad/modules/tcl/init/bash
    module load base; module load vcs
fi
aha test apps/pointwise |& tee test.log
t_test=$(( `date +%s` - $t_start ))
echo "Pointwise test took $t_test seconds"

# SUMMARY 1
# 
# Initial garnet build                   640 seconds
# ---------------------------------  -----------
# Pointwise 'compile' (map)               60 seconds
# Pointwise 'compile' (pnr) w/o daemon   135 seconds
# Pointwise 'compile' (pnr) w/ daemon     68 seconds
# Pointwise test                           9 seconds
# Pointwise total, daemon                137 seconds
# Pointwise total, no daemon             204 seconds

t_total_daemon=$((   $t_map + $t_pnr_daemon    + $t_test))
t_total_no_daemon=$(($t_map + $t_pnr_no_daemon + $t_test))

fmt="%-37s %4d seconds\n"
printf "$fmt" "Initial garnet build"  $t_garnet;\
printf "%s  %s\n" "---------------------------------" "-----------";\
printf "$fmt" "Pointwise 'compile' (map)"  $t_map;\
printf "$fmt" "Pointwise 'compile' (pnr) w/o daemon"  $t_pnr_no_daemon;\
printf "$fmt" "Pointwise 'compile' (pnr) w/ daemon"  $t_pnr_daemon;\
printf "$fmt" "Pointwise test"  $t_test;\
printf "$fmt" "Pointwise total, daemon"  $t_total_daemon; \
printf "$fmt" "Pointwise total, no daemon"  $t_total_no_daemon

# SUMMARY 2
# 
# Step                 Total(d)    Compile(d)   Map(d)     Test(d) 
# ------------------- ----------   ----------  --------   ---------
# garnet               640 (640) 
# apps/pointwise       204 (137)    60 (60)    135 (68)      9 (9)   

printf "%s\n" "Step                 Total(d)    Compile(d)   Map(d)     Test(d) " ;\
printf "%s\n" "------------------- ----------   ----------  --------   ---------" ;\
printf "%-19s %4s %-6s\n" garnet $t_garnet "($t_garnet)" ;\
printf "%-19s %4s %-6s %4s %-6s %4s %-6s %4s %-6s\n" \
       $app \
       $t_total_no_daemon "($t_total_daemon)" \
       $t_map             "($t_map)" \
       $t_pnr_no_daemon   "($t_pnr_daemon)" \
       $t_test            "($t_test)"
