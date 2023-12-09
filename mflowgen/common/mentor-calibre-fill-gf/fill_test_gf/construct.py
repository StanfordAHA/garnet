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
    print('Error: fill_test requires design_name input parameter')
    sys.exit(1)

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  parameters = {
    'design_name' : design_name,
    'drc_env_setup' : 'drcenv-block-den-only.sh'
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  # Custom steps
  checker   = Step( this_dir + '/checker' )

  # Default steps
  drc = Step( 'mentor-calibre-drc', default=True )

  # Add graph inputs and outputs so this can be used in hierarchical flows

  # Inputs
  g.add_input( 'fill.gds', \
               drc.i( 'design_merged.gds' )
             )
  g.add_input( 'adk', \
               drc.i( 'adk' )
             )

  g.add_output( 'result', checker.o( 'result' ) )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( drc       )
  g.add_step( checker   )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name
  g.connect_by_name( drc, checker )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  return g


if __name__ == '__main__':
  g = construct()

