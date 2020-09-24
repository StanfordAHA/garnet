#=========================================================================
# report-special-timing.py
#=========================================================================
# Additional timing reports for special paths (e.g., feedthroughs) that we
# want to parse using mflowgen assertions.
#

# Clock passthrough

report_timing -from clk_pass_through \
              -to   clk_pass_through_out* \
              > reports/time-clock-passthrough.rpt

