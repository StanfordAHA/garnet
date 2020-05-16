#=========================================================================
# test_timing.py
#=========================================================================
# Additional timing assertions for special paths (e.g., feedthroughs)
#

#-------------------------------------------------------------------------
# tests
#-------------------------------------------------------------------------

def test_clk_pass_through_arrival():
  rpt = 'reports/time-clock-passthrough.rpt'
  #assert arrival( rpt ) >= 0.030 # clock must pass through >= 0.030 ns
  #assert arrival( rpt ) <= 0.052 # clock must pass through <= 0.052 ns



#-------------------------------------------------------------------------
# slack
#-------------------------------------------------------------------------
# Reads a timing report (dc or innovus) and returns the slack (for the
# first path) as a float.
#

def slack( rpt ):

  # Read the timing report

  with open( rpt ) as f:
    lines = [ l for l in f.readlines() if 'slack' in l.lower() ]

  # Extract the slack
  #
  # Get the first line with a slack number, which looks like this for DC:
  #
  #     slack (MET)              0.0195
  #
  # It looks like this for Innovus:
  #
  #     = Slack Time                    0.020
  #

  output = float( lines[0].split()[-1] )

  return output

#-------------------------------------------------------------------------
# arrival
#-------------------------------------------------------------------------
# Reads a timing report and returns the arrival time (for the first path)
# as a float.
#

def arrival( rpt ):

  # Read the timing report

  with open( rpt ) as f:
    lines = [ l for l in f.readlines() if 'arrival time' in l.lower() ]

  # To allow us to use this function to extract the arrival times in both
  # DC/Innovus timing reports, we filter out certain kinds of lines from
  # the Innovus timing report, which would normally look like this:
  #
  #     Other End Arrival Time          0.000
  #     = Beginpoint Arrival Time       10.009
  #

  lines = [ l for l in lines if 'Other End'  not in l ]
  lines = [ l for l in lines if 'Beginpoint' not in l ]

  # Extract the arrival time
  #
  # Get the first line with an arrival time, which looks like this for
  # DC:
  #
  #     data arrival time        0.0305
  #
  #     > Note that there is usually another "negative" version of this
  #     number just below, where the report shows its math:
  #
  #         data required time       0.0500
  #         data arrival time       -0.0305
  #
  #     > We want the first number, not this one.
  #
  # It looks like this for Innovus:
  #
  #     - Arrival Time                  0.031
  #

  output = float( lines[0].split()[-1] )

  return output


