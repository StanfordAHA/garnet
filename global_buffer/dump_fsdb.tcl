dump -file global_buffer.fsdb -type FSDB
dump -add top.dut -fsdb_opt +mda+packedmda+struct
run
exit
