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

def construct():

  g = Graph()

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  adk_name = 'tsmc16'
  adk_view = 'multivt'
  pwr_aware = False

  parameters = {
    'construct_path'    : __file__,
    'design_name'       : os.environ.get('design_name'),
    'clock_period'      : float(os.environ.get('clock_period')),
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    'PWR_AWARE'         : "False",#os.environ.get('PWR_AWARE'),
    'testbench_name'    : os.environ.get('testbench_name'),
    'strip_path'        : os.environ.get('strip_path'),
    'waves'             : os.environ.get('waves'),
    'use_sdf'           : os.environ.get('use_sdf'),
    'tile_id'           : os.environ.get('tile_id')
    }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  garnet_home = os.environ.get('GARNET_HOME')

  setup          = Step( garnet_home + '/mflowgen/common/tile-post-synth-power/setup' )
  synth_sim      = Step( garnet_home + '/mflowgen/common/cadence-xcelium-sim'         )
  pt_power_synth = Step( garnet_home + '/mflowgen/common/synopsys-ptpx-synth'         )

  synth_sim.extend_inputs( ['test_vectors.txt', 'test_outputs.txt', 'design.v'] )

  design = os.environ.get('design_name')
  if design == "Tile_MemCore":
      synth_sim.extend_inputs( ['sram.v'] )
      pt_power_synth.extend_inputs( ['sram_tt.db'] )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step(setup)
  g.add_step(synth_sim)
  g.add_step(pt_power_synth)

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  g.connect_by_name(adk, synth_sim)
  g.connect_by_name(adk, pt_power_synth)
  g.connect_by_name(setup, synth_sim)
  g.connect_by_name(setup, pt_power_synth)
  g.connect_by_name(synth_sim, pt_power_synth)

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  return g

if __name__ == '__main__':
  g = construct()
