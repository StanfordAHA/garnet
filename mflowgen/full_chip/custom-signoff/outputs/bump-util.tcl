# NOTE Needs stylus compatibility procs

# . -> Empty
# V -> Core VDD
# G -> Core VSS
# o -> IOVDD
# g -> IOVSS
# d -> Diff Pair (Data)
set bump_types {
    "dddddddddddddddddddddddd"
    "dgdddddddddd.ddddddddddgd"
    "dddddddddddddddddddddddd"
    "dgdddddddddd.ddddddddddgd"
    "ggggggggggggggggggggggg."
    "ogoooooooooo.oooooooooogo"
    "ggoddddddddddddddddddogg"
    "dgdddddddddd.ddddddddddgd"
    "ddoddddddddddddddddddodd"
    "dgdddddddddd.ddddddddddgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "........................."
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdddddddddd.ddddddddddgd"
    "ddoddddddddddddddddddodd"
    "dgdddddddddd.ddddddddddgd"
    "ggoddddddddddddddddddogg"
    "ogoooooooooo.oooooooooogo"
    "gggggggggggggggggggggggg"
    "dgdddddddddd.ddddddddddgd"
    "dddddddddddddddddddddddd"
    "dgdddddddddd.ddddddddddgd"
    "dddddddddddddddddddddddd"
}


proc bumps_of_type {bump_array type} {
    set bump_index 1
    set bump_list {}
    foreach type_char [split [join [lreverse $bump_array] ""] {}] {
	    if {$type_char == $type} {
	        lappend bump_list "Bump_${bump_index}.*"
	    }
	    incr bump_index
    }
    return $bump_list
}
