#! /usr/bin/env python
#=========================================================================
# construct.py
#=========================================================================
# Author :
# Date   :
#

import os
import sys

from mflowgen.components import Graph, Step
from shutil import which
from common.get_sys_adk import get_sys_adk

def construct(design_name='undefined', clock_period=1000):

  g = Graph()

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  parameters = {
    'design_name': design_name,
    'clock_period': clock_period
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  # Custom steps
  lvs_rules = Step( this_dir + '/custom-lvs-rules' )
  checker   = Step( this_dir + '/checker' )
  edit_netlist = Step( this_dir + '/cadence-genus-edit-netlist' )

  # Default steps
  lvs = Step( 'mentor-calibre-lvs', default=True )

  # Add graph inputs and outputs so this can be used in hierarchical flows

  # Inputs
  g.add_input( 'adk', \
               lvs.i( 'adk' ), \
               edit_netlist.i( 'adk' ) \
             )
  g.add_input( 'design.lvs.v', \
               edit_netlist.i( 'design.v' ), \
             )
  g.add_input( 'design-merged.gds', \
               lvs.i( 'design_merged.gds' ), \
             )

  g.add_output( 'result', checker.o( 'result' ) )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( lvs_rules    )
  g.add_step( edit_netlist )
  g.add_step( lvs          )
  g.add_step( checker      )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connections
  g.connect( edit_netlist.o( 'design.v' ), lvs.i( 'design.lvs.v' ) )

  # Connect by name
  g.connect_by_name( lvs_rules, lvs )
  g.connect_by_name( lvs, checker )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  return g


if __name__ == '__main__':
  g = construct()

