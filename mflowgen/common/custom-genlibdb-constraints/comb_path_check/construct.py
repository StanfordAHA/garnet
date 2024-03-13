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

def construct(**kwargs):

  g = Graph()

  try:
    design_name = kwargs['design_name']
  except KeyError:
    print('Error: ir_test requires design_name input parameter')
    sys.exit(1)

  try:
    clock_period = kwargs['clock_period']
  except KeyError:
    clock_period = 2000

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
  lib_timing_arcs = Step( this_dir + 'synopsys-pt-get-lib-timing-arcs' )
  checker         = Step( this_dir + '/checker' )

  # Default steps

  # Add graph inputs and outputs so this can be used in hierarchical flows

  # Inputs
  g.add_input( 'design.lib', \
               lib_timing_arcs.i( 'design.lib' ), \
             )

  g.add_output( 'result', checker.o( 'result' ) )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( static_pa )
  g.add_step( static_ra )
  g.add_step( checker   )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name
  g.connect_by_name( static_pa, static_ra )
  g.connect_by_name( static_ra, checker   )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  return g


if __name__ == '__main__':
  g = construct()

