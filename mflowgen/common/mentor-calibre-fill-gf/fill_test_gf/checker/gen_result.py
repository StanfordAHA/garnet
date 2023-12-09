#=========================================================================
# gen_result.py
#=========================================================================
# Parses the DRC results and determines whether fill passed or failed
#
# Author : Alex Carsello
# Date   : Dec. 8, 2023
#

# Grab the report
report_file = 'inputs/drc.summary'
with open(report_file) as f:
  lines = [line for line in f]

# Get the relevant lines within the ir drop section
for line in lines:
  if 'TOTAL DRC Results Generated:' in line:
    num_violations_line = line.rstrip('\n')

# If num violations is 0, the test passes
num_violations = int(num_violations_line.split(' ')[-2])

# Write to results file
with open('outputs/result', 'w') as f:
  if num_violations > 1:
    f.write("FAIL\n\n")
  else:
    f.write("PASS\n\n")


