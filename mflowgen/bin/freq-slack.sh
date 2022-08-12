#!/bin/bash

# To test:
#     ssh r7arm-aha; cd /build/gold; $0

# function find-frequency {
function find-clock-period {
    c=`find * -path '*signoff/results/'$1'.pt.sdc' | head -1`
    # echo Found constraint $c
    if ! [ "$c" ]; then
        # echo "- no info for $1 -"
        return
    fi
    

    # Find clock period and frequency
    ck=`egrep 'create_clock|period' $c | egrep 'ideal|MASTER'`
    cp=`echo $ck | sed 's/.*period //' | awk '{print $1}'`
    echo $cp

#     echo ""
}

# Sample signoff hold summary
# +--------------------+---------+---------+---------+---------+---------+---------+---------+---------+
# |     Hold mode      |   all   | default |All2Macro| In2Out  | In2Reg  |Macro2All| Reg2Out | Reg2Reg |
# +--------------------+---------+---------+---------+---------+---------+---------+---------+---------+
# |           WNS (ns):|  0.014  |  0.000  |  0.014  |  0.823  |  0.262  |  0.036  |  0.216  |   N/A   |
# |           TNS (ns):|  0.000  |  0.000  |  0.000  |  0.000  |  0.000  |  0.000  |  0.000  |   N/A   |
# |    Violating Paths:|    0    |    0    |    0    |    0    |    0    |    0    |    0    |   N/A   |
# |          All Paths:|2.06e+05 |    0    |  17152  |   32    |  22528  |1.66e+05 |   576   |   N/A   |
# +--------------------+---------+---------+---------+---------+---------+---------+---------+---------+

function get-slack {
    # E.g. 
    # ptsd = 19-tile_array/28-cadence-innovus-signoff/results/Interconnect.pt.sdc
    # headhead = 19-tile_array/28-cadence-innovus-signoff/
    # slack_report = 19-tile_array/28-cadence-innovus-signoff/signoff_hold.summary
    m=$1
    ptsd=`find * -path '*signoff/results/'$m'.pt.sdc' | head -1`
    head=`echo $ptsd | sed 's,[^/]*$,,'`
    headhead=`echo $head | sed 's,/[^/]*/$,,'`
    slack_report=${headhead}/reports/signoff_hold.summary

    WNS=`grep WNS $slack_report | sed 's/|/ /' | awk '{print $3}'`
    echo $WNS
}

echo 'Module            Target Frequency     WNS => Actual Freq'
echo '-------------------------------------------------------------'
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

    # Clock period and frequency
    cp=`find-clock-period $design`
    freq=`echo 1000/$cp | bc`
    printf "%-17s %4d MHz (%4.2fns)  " $mod $freq $cp

    # Slack
    WNS=`get-slack $design`
    printf "%6s" $WNS

    # Actual freq
    # echo "scale=3; 1000/($cp - $WNS)"
    actual_freq=`echo "scale=3; 1000/($cp - $WNS)" | bc`
    actual_freq=`echo "1000/($cp - $WNS)" | bc`
    # echo "    $actual_freq MHz"
    printf "  => %4d MHz" $actual_freq


    echo ""



done
echo '-------------------------------------------------'
echo '  * Clock speed from *-signoff/results/*.pt.sdc'
echo '  * Slack from */reports/postroute_all.tarpt'

##############################################################################
exit
##############################################################################

function get_reports { find * | grep postroute/reports/postroute_all.tarpt; }

echo -n "tile_array slack "; get_slack Interconnect


# soc=`get_reports | grep SOC`; echo $soc

function get-slack-postroute {
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

