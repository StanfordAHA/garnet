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
  adk_view = 'stdview'

  parameters = {
    'construct_path' : __file__,
    'design_name'    : 'global_buffer',
    'clock_period'   : 1.0,
    'adk'            : adk_name,
    'adk_view'       : adk_view,
    # Synthesis
    'flatten_effort' : 3,
    'topographical'  : True,
    # hold target slack
    'hold_target_slack'   : 0.045,
    'num_tile_array_cols' : 32,
    'num_glb_tiles'       : 16,
    # glb tile memory size (unit: KB)
    'glb_tile_mem_size' : 256
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl               = Step( this_dir + '/rtl'                                 )
  sim               = Step( this_dir + '/sim'                                 )
  glb_tile          = Step( this_dir + '/glb_tile'                            )
  glb_tile_rtl      = Step( this_dir + '/glb_tile_rtl'                        )
  glb_tile_syn      = Step( this_dir + '/glb_tile_syn'                        )
  constraints       = Step( this_dir + '/constraints'                         )
  custom_init       = Step( this_dir + '/custom-init'                         )
  custom_lvs        = Step( this_dir + '/custom-lvs-rules'                    )
  custom_power      = Step( this_dir + '/../common/custom-power-hierarchical' )

  # Default steps

  info           = Step( 'info',                            default=True )
  synth          = Step( 'cadence-genus-synthesis',         default=True )
  iflow          = Step( 'cadence-innovus-flowsetup',       default=True )
  init           = Step( 'cadence-innovus-init',            default=True )
  power          = Step( 'cadence-innovus-power',           default=True )
  place          = Step( 'cadence-innovus-place',           default=True )
  cts            = Step( 'cadence-innovus-cts',             default=True )
  postcts_hold   = Step( 'cadence-innovus-postcts_hold',    default=True )
  route          = Step( 'cadence-innovus-route',           default=True )
  postroute      = Step( 'cadence-innovus-postroute',       default=True )
  postroute_hold = Step( 'cadence-innovus-postroute_hold',  default=True )
  signoff        = Step( 'cadence-innovus-signoff',         default=True )
  pt_signoff     = Step( 'synopsys-pt-timing-signoff',      default=True )
  genlib         = Step( 'cadence-genus-genlib',            default=True )
  if which("calibre") is not None:
      drc            = Step( 'mentor-calibre-drc',            default=True )
      lvs            = Step( 'mentor-calibre-lvs',            default=True )
  else:
      drc            = Step( 'cadence-pegasus-drc',           default=True )
      lvs            = Step( 'cadence-pegasus-lvs',           default=True )
  debugcalibre   = Step( 'cadence-innovus-debug-calibre',   default=True )

  # Add (dummy) parameters to the default innovus init step

  init.update_params( {
    'core_width'  : 0,
    'core_height' : 0
    }, allow_new=True )

  # Add glb_tile macro inputs to downstream nodes

  pt_signoff.extend_inputs( ['glb_tile.db'] )

  # These steps need timing info for glb_tiles
  tile_steps = \
    [ synth, iflow, init, power, place, cts, postcts_hold,
      route, postroute, postroute_hold, signoff, genlib ]

  for step in tile_steps:
    step.extend_inputs( ['glb_tile_tt.lib', 'glb_tile.lef'] )

  # Need the glb_tile gds to merge into the final layout

  signoff.extend_inputs( ['glb_tile.gds'] )

  # Need glb_tile lvs.v file for LVS

  lvs.extend_inputs( ['glb_tile.lvs.v'] )

  # Need sram spice file for LVS

  lvs.extend_inputs( ['sram.spi'] )

  xlist = synth.get_postconditions()
  xlist = \
    [ _ for _ in xlist if 'percent_clock_gated' not in _ ]
  xlist = synth.set_postconditions( xlist )

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  sim.extend_inputs( ['design.v'] )
  sim.extend_inputs( ['glb_tile.v'] )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info           )
  g.add_step( rtl            )
  g.add_step( sim            )
  g.add_step( glb_tile       )
  g.add_step( glb_tile_rtl   )
  g.add_step( glb_tile_syn   )
  g.add_step( constraints    )
  g.add_step( synth          )
  g.add_step( iflow          )
  g.add_step( init           )
  g.add_step( custom_init    )
  g.add_step( power          )
  g.add_step( custom_power   )
  g.add_step( place          )
  g.add_step( cts            )
  g.add_step( postcts_hold   )
  g.add_step( route          )
  g.add_step( postroute      )
  g.add_step( postroute_hold )
  g.add_step( signoff        )
  g.add_step( pt_signoff     )
  g.add_step( genlib         )
  g.add_step( drc            )
  g.add_step( lvs            )
  g.add_step( custom_lvs     )
  g.add_step( debugcalibre   )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( adk,      synth             )
  g.connect_by_name( adk,      iflow          )
  g.connect_by_name( adk,      init           )
  g.connect_by_name( adk,      power          )
  g.connect_by_name( adk,      place          )
  g.connect_by_name( adk,      cts            )
  g.connect_by_name( adk,      postcts_hold   )
  g.connect_by_name( adk,      route          )
  g.connect_by_name( adk,      postroute      )
  g.connect_by_name( adk,      postroute_hold )
  g.connect_by_name( adk,      signoff        )
  g.connect_by_name( adk,      drc            )
  g.connect_by_name( adk,      lvs            )

  g.connect_by_name( glb_tile,      synth           )
  g.connect_by_name( glb_tile,      iflow        )
  g.connect_by_name( glb_tile,      init         )
  g.connect_by_name( glb_tile,      power        )
  g.connect_by_name( glb_tile,      place        )
  g.connect_by_name( glb_tile,      cts          )
  g.connect_by_name( glb_tile,      postcts_hold )
  g.connect_by_name( glb_tile,      route        )
  g.connect_by_name( glb_tile,      postroute    )
  g.connect_by_name( glb_tile,      postroute_hold )
  g.connect_by_name( glb_tile,      signoff      )
  g.connect_by_name( glb_tile,      pt_signoff   )
  g.connect_by_name( glb_tile,      genlib       )
  g.connect_by_name( glb_tile,      drc          )
  g.connect_by_name( glb_tile,      lvs          )

  g.connect_by_name( rtl,         sim        )
  g.connect_by_name( glb_tile_rtl,         sim        )

  g.connect_by_name( rtl,         synth        )
  g.connect_by_name( constraints, synth        )

  # glb_tile can use the same rtl as glb_top
  g.connect_by_name( rtl,         glb_tile      )

  g.connect_by_name( synth,       iflow        )
  g.connect_by_name( synth,       init         )
  g.connect_by_name( synth,       power        )
  g.connect_by_name( synth,       place        )
  g.connect_by_name( synth,       cts          )

  g.connect_by_name( iflow,    init         )
  g.connect_by_name( iflow,    power        )
  g.connect_by_name( iflow,    place        )
  g.connect_by_name( iflow,    cts          )
  g.connect_by_name( iflow,    postcts_hold )
  g.connect_by_name( iflow,    route        )
  g.connect_by_name( iflow,    postroute    )
  g.connect_by_name( iflow,    postroute_hold )
  g.connect_by_name( iflow,    signoff      )

  g.connect_by_name( custom_init,  init     )
  g.connect_by_name( custom_power, power    )
  g.connect_by_name( custom_lvs,   lvs      )

  g.connect_by_name( init,         power          )
  g.connect_by_name( power,        place          )
  g.connect_by_name( place,        cts            )
  g.connect_by_name( cts,          postcts_hold   )
  g.connect_by_name( postcts_hold, route          )
  g.connect_by_name( route,        postroute      )
  g.connect_by_name( postroute,    postroute_hold )
  g.connect_by_name( postroute_hold,    signoff   )
  g.connect_by_name( signoff,      drc            )
  g.connect_by_name( signoff,      lvs            )
  g.connect(signoff.o('design-merged.gds'), drc.i('design_merged.gds'))
  g.connect(signoff.o('design-merged.gds'), lvs.i('design_merged.gds'))

  g.connect_by_name( adk,          pt_signoff     )
  g.connect_by_name( signoff,      pt_signoff     )

  g.connect_by_name( adk,          genlib   )
  g.connect_by_name( signoff,      genlib   )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( synth,       debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( drc,      debugcalibre )
  g.connect_by_name( lvs,      debugcalibre )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

  # pin assignment parameters update
  init.update_params( { 'num_tile_array_cols': parameters['num_tile_array_cols'] }, allow_new=True )
  init.update_params( { 'num_glb_tiles': parameters['num_glb_tiles'] }, allow_new=True )

  # Change nthreads
  synth.update_params( { 'nthreads': 4 } )
  iflow.update_params( { 'nthreads': 4 } )

  order = init.get_param('order') # get the default script run order
  reporting_idx = order.index( 'reporting.tcl' ) # find reporting.tcl
  # Add dont-touch before reporting
  order.insert ( reporting_idx, 'dont-touch.tcl' )
  init.update_params( { 'order': order } )

  # Increase hold slack on postroute_hold step
  postroute_hold.update_params( { 'hold_target_slack': parameters['hold_target_slack'] }, allow_new=True  )

  # useful_skew
  cts.update_params( { 'useful_skew': False }, allow_new=True )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


