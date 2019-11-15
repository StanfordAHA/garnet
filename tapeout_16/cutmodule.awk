#!/usr/bin/awk -f

BEGIN { argc=ARGC; for (i in ARGV) {argv[i] = ARGV[i]; delete ARGV[i] } }
BEGIN { modname = argv[1] }

($1 == "module") && ($2 == modname) {
    cut = 1
}
cut != 1 {
    print $0 
}
cut == 1 {
    print "//", $0
}
$1 == "endmodule" {
    cut = 0
}
