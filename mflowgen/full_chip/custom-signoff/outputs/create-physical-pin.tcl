source inputs/bump-util.tcl

set signal_bumps [bumps_of_type $bump_types "d"]
foreach bump $signal_bumps {
    set bump_name [dbGet top.bumps.name $bump]
    set bump_net [string range [dbGet -e [dbGet -p top.bumps.name $bump_name].net.name] 1 end-1]
    if {[string match "pad_*" $bump_net]} {
        echo $bump_name $bump_net
        createPhysicalPin $bump_net -net $bump_net -rect [dbGet -e [dbGet -p top.bumps.name $bump_name].bump_shape_bbox] -layer gmb
    }
}

set ground_bumps [bumps_of_type $bump_types "G"]
foreach bump $ground_bumps {
    set bump_name [dbGet top.bumps.name $bump]
    set bump_net VSS
    createPhysicalPin $bump_net -net $bump_net -rect [dbGet -e [dbGet -p top.bumps.name $bump_name].bump_shape_bbox] -layer gmb
}

set power_bumps [bumps_of_type $bump_types "V"]
foreach bump $power_bumps {
    set bump_name [dbGet top.bumps.name $bump]
    set bump_net VDD
    createPhysicalPin $bump_net -net $bump_net -rect [dbGet -e [dbGet -p top.bumps.name $bump_name].bump_shape_bbox] -layer gmb
}

set ioground_bumps [bumps_of_type $bump_types "g"]
foreach bump $ioground_bumps {
    set bump_name [dbGet top.bumps.name $bump]
    set bump_net VSS
    createPhysicalPin $bump_net -net $bump_net -rect [dbGet -e [dbGet -p top.bumps.name $bump_name].bump_shape_bbox] -layer gmb
}

set iopower_bumps [bumps_of_type $bump_types "o"]
foreach bump $iopower_bumps {
    set bump_name [dbGet top.bumps.name $bump]
    set bump_net VDDPST
    createPhysicalPin $bump_net -net $bump_net -rect [dbGet -e [dbGet -p top.bumps.name $bump_name].bump_shape_bbox] -layer gmb
}
