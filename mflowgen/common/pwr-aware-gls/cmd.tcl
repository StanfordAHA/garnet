#database -open -vcd vcddb -into verilog.vcd -default -timescale ps
#probe -create -all -vcd -depth all
run 500ns
quit
