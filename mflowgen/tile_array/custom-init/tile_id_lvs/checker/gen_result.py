#=========================================================================
# gen_result.py
#=========================================================================
# Parses the results from static IR analysis and determines whether
# or not the test passes or fails.
#
# Author : Alex Carsello
# Date   : Nov. 17, 2023
#

from mflowgen.assertions.assertion_classes import File
# Grab the report
report_file = 'inputs/lvs.report'

with open('outputs/result', 'w') as f:
  if 'LVS CORRECT' in File(report_file):
    f.write("PASS\n\n")
  else:
    f.write("FAIL\n\n")

  f.writelines(ir_drop_lines)

