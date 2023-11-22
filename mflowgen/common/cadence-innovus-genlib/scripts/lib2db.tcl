
enable_write_lib_mode
read_lib ../outputs/design.lib
write_lib -format db $::env(design_name) -output ../outputs/design.db
exit
