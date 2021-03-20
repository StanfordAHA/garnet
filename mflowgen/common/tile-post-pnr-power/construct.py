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
    'PWR_AWARE'         : os.environ.get('PWR_AWARE'),
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

  setup          = Step( garnet_home + '/mflowgen/common/tile-post-pnr-power/setup' )
  gl_sim         = Step( garnet_home + '/mflowgen/common/cadence-xcelium-sim'       )
  pt_power_gl    = Step( garnet_home + '/mflowgen/common/synopsys-ptpx-gl'          )

  gl_sim.extend_inputs( ['test_vectors.txt', 'test_outputs.txt', 'design.v'] )

  if os.environ.get('PWR_AWARE') == 'True':
      gl_sim.extend_inputs( ["design.vcs.pg.v"] )

  design = os.environ.get('design_name')
  if design == 'Tile_MemCore':
      if os.environ.get('PWR_AWARE') == 'True':
          gl_sim.extend_inputs( ['sram-pwr.v'] )
      else:
          gl_sim.extend_inputs( ['sram.v'] )
      pt_power_gl.extend_inputs( ['sram_tt.db'] )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step(setup)
  g.add_step(gl_sim)
  g.add_step(pt_power_gl)

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  g.connect_by_name(adk, gl_sim)
  g.connect_by_name(adk, pt_power_gl)
  g.connect_by_name(setup, gl_sim)
  g.connect_by_name(setup, pt_power_gl)
  g.connect_by_name(gl_sim, pt_power_gl)

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  return g

if __name__ == '__main__':
  g = construct()
