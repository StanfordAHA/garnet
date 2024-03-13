#=========================================================================
# gen_result.py
#=========================================================================
# Parses the results from static IR analysis and determines whether
# or not the test passes or fails.
#
# Author : Alex Carsello
# Date   : Nov. 17, 2023
#

# Grab the report
report_file = 'inputs/static_rail_analysis_results/VDD_static_rail/VDD_25C_avg_1/Reports/VDD.main.html.rpt'
with open(report_file) as f:
  lines = [line for line in f]

# Find the IR Drop Analysis section of the report
ir_drop_index = lines.index('IR DROP ANALYSIS\n')
# The next section after IR drop in the report is
# effective resistance analysis
era_index = lines.index('EFFECTIVE RESISTANCE ANALYSIS\n')

# Just get the lines relevant to ir drop analysis
ir_drop_lines = lines[ir_drop_index:era_index-2]

# Get the relevant lines within the ir drop section
for line in ir_drop_lines:
  if 'Number of Violations:' in line:
    num_violations_line = line.rstrip('\n')

# If num violations is 0, the test passes
num_violations = int(num_violations_line.split(' ')[-1])

# Write to results file
with open('outputs/result', 'w') as f:
  if num_violations > 0:
    f.write("FAIL\n\n")
  else:
    f.write("PASS\n\n")

  f.writelines(ir_drop_lines)

