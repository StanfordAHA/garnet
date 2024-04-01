#=========================================================================
# gen_result.py
#=========================================================================
# Parses the results from static IR analysis and determines whether
# or not the test passes or fails.
#
# Author : Alex Carsello
# Date   : Nov. 17, 2023
#

import sys

# Grab the report
report_file = 'inputs/lib_timing_arcs'
with open(report_file) as f:
  lines = [line for line in f]

# Find the timing arc section of the report
for i, line in enumerate(lines):
  if 'Arc Pins' in line:
    arcs_start = i + 3
    break
try:
  arcs_start
except:
  print("Error: Arcs section not found in input report. Exiting.")
  sys.exit(1)

arc_lines = lines[arcs_start:-3]

# Get the relevant lines within the ir drop section
split_entry = False
illegal_arcs = []
for line in arc_lines:
  split_line = line.split(' ')
  # Handle case where arc entry is 2 lines long.
  # In this case, the start and endpoint are on
  # The following line.
  if split_entry:
    # Processing 2nd line of split entry
    startpoint = split_line[0]
    endpoint = split_line[1]
    split_entry = False
  elif len(split_line) < 4:
    # We've found a split entry
    split_entry = True
    continue
  else:
    startpoint = split_line[2]
    endpoint = split_line[3]

  # Check to see if arc is SB->SB (illegal combinational path)
  if 'SB' in startpoint and 'SB' in endpoint:
    illegal_arcs.append((startpoint, endpoint))


# If num violations is 0, the test passes
num_violations = len(illegal_arcs)

# Write to results file
with open('outputs/result', 'w') as f:
  if num_violations > 0:
    f.write("FAIL\n\n")
    f.write("SB->SB combinational arcs:\n")
    for arc in illegal_arcs:
      print(f"{arc}\n")
  else:
    f.write("PASS\n\n")


