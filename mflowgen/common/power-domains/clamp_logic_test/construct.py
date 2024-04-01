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

def construct(design_name='undefined'):

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
  check_clamp_logic = Step( this_dir + '/cadence-innovus-check-clamp-logic' )

  # Default steps

  # Add graph inputs and outputs so this can be used in hierarchical flows

  # Inputs
  g.add_input( 'innovus-foundation-flow', \
               check_clamp_logic.i( 'design.lib' ), \
             )
  g.add_input( 'design.checkpoint', \
               check_clamp_logic.i( 'design.lib' ), \
             )
  g.add_input( 'adk', \
               check_clamp_logic.i( 'design.lib' ), \
             )

  g.add_output( 'result', check_clamp_logic.o( 'result' ) )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( check_clamp_logic )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  return g


if __name__ == '__main__':
  g = construct()

