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

def construct():

  g = Graph()

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  parameters = {
    'design_name': 'global_controller',
    'clock_period': 1.0
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  # Custom steps

  # Default steps
  static_pa = Step( 'cadence-voltus-static-power-analysis', default=True )
  static_ra = Step( 'cadence-voltus-static-rail-analysis', default=True )

  # Add graph inputs and outputs so this can be used in hierarchical flows

  # Inputs
  g.add_input( 'design.checkpoint', \
               static_pa.i( 'design.checkpoint' ), \
               static_ra.i( 'design.checkpoint' ) \
             )
  g.add_input( 'design.sdc', \
               static_pa.i( 'design.sdc' ), \
               static_ra.i( 'design.sdc' ) \
             )
  g.add_input( 'adk', \
               static_pa.i( 'adk' ),
               static_ra.i( 'adk' ) \
             )

  g.add_output( 'static_rail_analysis_results', static_ra.o( 'static_rail_analysis_results' ) )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( static_pa )
  g.add_step( static_ra )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name
  g.connect_by_name( static_pa, static_ra )


  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  return g


if __name__ == '__main__':
  g = construct()

