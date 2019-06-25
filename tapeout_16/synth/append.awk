#!/usr/bin/awk -f

BEGIN { argc=ARGC; for (i in ARGV) {argv[i] = ARGV[i]; delete ARGV[i] } }
BEGIN { prefix = argv[1] }

$1 == "module" {
    print $1, prefix $2, $3
}
$1 != "module" {
    print $0
}
