# Parse the bump map CSV
# Author: B. Richards 4/13/2017
#

unassign_bumps -all

set fid [open [get_db flow_source_directory]/bumps.csv]
set content [read $fid]
close $fid

set records [split $content "\n"]

set bump_num 1
set num_rows 26
set row $num_rows
foreach rec $records {
    set col 1
    set fields [split $rec ","]
    foreach field $fields {
	set bump_num [expr ($row - 1) * 26 + $col]
	set bump_name "Bump_$bump_num.$row.$col"

	switch -glob $field {
	    IBIAS {
		puts "Skipping IP net $field"
	    }
	    SD_* {
		set field [string map {SD_ serdes_} $field]
		assign_signal_to_bump -bump $bump_name -net "io_$field"
	    }
	    VIN -
	    VIP {
		set field [string map {SD_ serdes_} $field]
		assign_signal_to_bump -bump $bump_name -net "$field"
	    }
	    VIO {
		set field VDDPST
		select_bump -bumps $bump_name
		assign_pg_bumps -connect_type ioring -selected -nets "$field"
	    }
	    VDDADC -
	    VDDHADC -
	    *DVDD* -
	    *AVDD* -
	    TISAR* {
		select_bump -bumps $bump_name
		assign_pg_bumps -selected -nets "$field"
	    }
	    VDDPST {
		select_bump -bumps $bump_name
		assign_pg_bumps -connect_type ioring -selected -nets "$field"
	    }
	    VSS -
	    VDD {
		select_bump -bumps $bump_name
		assign_pg_bumps -connect_type ioring -selected -nets "$field"
	    }
	    VDD_1 -
	    VDD_2 -
	    VDD_3 -
	    VDD_4 -
	    VDD_5 -
	    VDD_6 {
		select_bump -bumps $bump_name
		assign_pg_bumps -connect_type ioring -selected -nets VDD
	    }
	    {} -
	    nc {
	    }
	    default {
		assign_signal_to_bump -bumps $bump_name -net "io_$field"
	    }
	}

	deselect_bumps

	incr col
	incr bump_num
    }
    incr row -1
}
puts "Rows: $num_rows"

