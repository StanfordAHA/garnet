#!/bin/bash

# To test:
#     ssh r7arm-aha; cd /build/gold; $0

function find-frequency {
    c=`find * -path '*signoff/results/'$1'.pt.sdc' | head -1`
    # echo Found constraint $c
    if ! [ "$c" ]; then
        # echo "- no info for $1 -"
        return
    fi
    

    # Reqriting filename => module-name e.g.
    # < "19-tile_array/28-cadence-innovus-signoff/results/Interconnect.pt.sdc"
    # > "tile_array"
    tail=`echo $c | sed 's,.*/,,'`
    module=`echo $tail | sed 's/.pt.sdc//'`
    module=`echo $module | sed 's/Interconnect/tile_array  /'`
    module=`echo $module | sed 's/GarnetSOC_pad_frame/GarnetSOC/'`

    # Find clock period and frequency
    ck=`egrep 'create_clock|period' $c | egrep 'ideal|MASTER'`
    cp=`echo $ck | sed 's/.*period //' | awk '{print $1}'`
    freq=`echo 1000/$cp | bc`

    # printf "%-20s %4.2f ns    %4d MHz\n" $module $cp $freq
    printf "%-20s %4d MHz    %4.2f ns" $module $freq $cp

#     echo ""
}

function get-slack {
    modname=$1
    reports=`find * | grep postroute/reports/postroute_all.tarpt`
    for r in $reports; do
        design=`awk '/Design/{print $NF; exit}' $r`
        if [ "$design" == "$modname" ]; then
            # echo Found report $r; 
            slack=`grep Slack $r | head -1 | awk '{print $NF}'`
            # echo Found slack $slack
            # echo $modname slack $slack
            echo $slack
            break
        fi
    done
}

echo 'Module                 Target Frequency     Slack'
echo '-------------------------------------------------'
for design in \
    GarnetSOC_pad_frame \
    global_controller \
    linebreak \
    global_buffer \
    glb_tile \
    linebreak \
    Interconnect \
    Tile_MemCore \
    Tile_PE \
    ; do

    if [ "$design" == "linebreak" ]; then
        echo ""; continue
    fi

    # filename => module-name e.g. "Interconnect" => "tile_array"
    mod=$design
    [ "$mod" == "Interconnect" ] && mod="tile_array"
    [ "$mod" == "GarnetSOC_pad_frame" ] && mod="GarnetSOC"
#     echo $mod

    find-frequency $design
    echo -n "   "
    get-slack $design

done
echo '-------------------------------------------------'
echo '  * Clock speed from *-signoff/results/*.pt.sdc'
echo '  * Slack from */reports/postroute_all.tarpt'

exit




function get_reports { find * | grep postroute/reports/postroute_all.tarpt; }

function get_slack {
    modname=$1
    reports=`find * | grep postroute/reports/postroute_all.tarpt`
    for r in $reports; do
        design=`awk '/Design/{print $NF; exit}' $r`
        if [ "$design" == "$modname" ]; then
            # echo Found report $r; 
            slack=`grep Slack $r | head -1 | awk '{print $NF}'`
            # echo Found slack $slack
            # echo $modname slack $slack
            echo $slack
            break
        fi
    done
}

echo -n "tile_array slack "; get_slack Interconnect


# soc=`get_reports | grep SOC`; echo $soc

exit

# 
# 
# % find * | grep postroute/reports/postroute_all.tarpt
# full_chip/19-tile_array/16-Tile_MemCore/22-cadence-innovus-postroute/reports/postroute_all.tarpt
# full_chip/19-tile_array/17-Tile_PE/23-cadence-innovus-postroute/reports/postroute_all.tarpt
# full_chip/19-tile_array/26-cadence-innovus-postroute/reports/postroute_all.tarpt
# full_chip/16-glb_top/8-glb_tile/17-cadence-innovus-postroute/reports/postroute_all.tarpt
# full_chip/16-glb_top/19-cadence-innovus-postroute/reports/postroute_all.tarpt
# full_chip/17-global_controller/14-cadence-innovus-postroute/reports/postroute_all.tarpt
# full_chip/31-cadence-innovus-postroute/reports/postroute_all.tarpt
# 
# for m in \
# tile_array/.*Tile_MemCore
# tile_array/.*Tile_PE
# tile_array/
# glb_top/8-glb_tile/17-
# glb_top/19-
# global_controller/14-
# 31-
#     
# 
# 
# 
# full_chip/19-tile_array/16-Tile_MemCore/22-cadence-innovus-postroute/reports/postroute_all.tarpt
# full_chip/19-tile_array/16-Tile_MemCore/22-cadence-innovus-postroute/reports/postroute_all.tarpt
# full_chip/19-tile_array/16-Tile_MemCore/22-cadence-innovus-postroute/reports/postroute_all.tarpt
# 
# 
# 
# 
# 
# 



exit


function find-frequency {
    c=`find * -path '*signoff/results/'$1'.pt.sdc' | head -1`
    # echo Found constraint $c

    # Reqriting filename => module-name e.g.
    # < "19-tile_array/28-cadence-innovus-signoff/results/Interconnect.pt.sdc"
    # > "tile_array"
    tail=`echo $c | sed 's,.*/,,'`
    module=`echo $tail | sed 's/.pt.sdc//'`
    module=`echo $module | sed 's/Interconnect/tile_array  /'`
    module=`echo $module | sed 's/GarnetSOC_pad_frame/GarnetSOC/'`

    # Find clock period and frequency
    ck=`egrep 'create_clock|period' $c | egrep 'ideal|MASTER'`
    cp=`echo $ck | sed 's/.*period //' | awk '{print $1}'`
    freq=`echo 1000/$cp | bc`
    printf "%-20s %4.2f ns    %4d MHz" $module $cp $freq
    echo ""
}

echo 'Clock speed from *signoff/results/*.pt.sdc'
echo '------------------------------------------'
find-frequency GarnetSOC_pad_frame
echo ""
find-frequency global_controller
find-frequency global_buffer
find-frequency glb_tile
echo ""
find-frequency Interconnect
find-frequency Tile_MemCore
find-frequency Tile_PE
echo '------------------------------------------'
exit


# Sample output:
# 
# Clock speed from *signoff/results/*.pt.sdc
# ------------------------------------------
# GarnetSOC            1.00 ns    1000 MHz
# 
# global_controller    1.00 ns    1000 MHz
# global_buffer        1.11 ns     900 MHz
# glb_tile             1.11 ns     900 MHz
# 
# tile_array           1.10 ns     909 MHz
# Tile_MemCore         1.10 ns     909 MHz
# Tile_PE              1.10 ns     909 MHz
# ------------------------------------------

# function find-frequencies {
#     constraints=`find * -path '*signoff/results/*.sdc'`
#     for c in $constraints; do 
#         find-frequency $c
#     done
# }
