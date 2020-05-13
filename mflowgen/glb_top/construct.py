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
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl          = Step( this_dir + '/rtl'                                 )
  glb_tile     = Step( this_dir + '/glb_tile'                            )
  constraints  = Step( this_dir + '/constraints'                         )
  custom_init  = Step( this_dir + '/custom-init'                         )
  custom_lvs   = Step( this_dir + '/custom-lvs-rules'                    )
  custom_power = Step( this_dir + '/../common/custom-power-hierarchical' )

  # Default steps

  info         = Step( 'info',                              default=True )
  # constraints  = Step( 'constraints',                       default=True )
  dc           = Step( 'synopsys-dc-synthesis',             default=True )
  iflow        = Step( 'cadence-innovus-flowsetup',         default=True )
  init         = Step( 'cadence-innovus-init',              default=True )
  power        = Step( 'cadence-innovus-power',             default=True )
  place        = Step( 'cadence-innovus-place',             default=True )
  cts          = Step( 'cadence-innovus-cts',               default=True )
  postcts_hold = Step( 'cadence-innovus-postcts_hold',      default=True )
  route        = Step( 'cadence-innovus-route',             default=True )
  postroute    = Step( 'cadence-innovus-postroute',         default=True )
  postroute_hold = Step( 'cadence-innovus-postroute_hold',  default=True )
  signoff      = Step( 'cadence-innovus-signoff',           default=True )
  pt_signoff   = Step( 'synopsys-pt-timing-signoff',        default=True )
  genlibdb     = Step( 'synopsys-ptpx-genlibdb',            default=True )
  gdsmerge     = Step( 'mentor-calibre-gdsmerge',           default=True )
  drc          = Step( 'mentor-calibre-drc',                default=True )
  lvs          = Step( 'mentor-calibre-lvs',                default=True )
  debugcalibre = Step( 'cadence-innovus-debug-calibre',     default=True )

  # Add (dummy) parameters to the default innovus init step

  init.update_params( {
    'core_width'  : 0,
    'core_height' : 0
    }, allow_new=True )

  # Add glb_tile macro inputs to downstream nodes

  dc.extend_inputs( ['glb_tile.db'] )
  pt_signoff.extend_inputs( ['glb_tile.db'] )
  genlibdb.extend_inputs( ['glb_tile.db'] )

  # These steps need timing info for glb_tiles

  tile_steps = \
    [ iflow, init, power, place, cts, postcts_hold,
      route, postroute, postroute_hold, signoff, gdsmerge ]

  for step in tile_steps:
    step.extend_inputs( ['glb_tile_tt.lib', 'glb_tile.lef'] )

  # Need the glb_tile gds to merge into the final layout

  gdsmerge.extend_inputs( ['glb_tile.gds'] )

  # Need glb_tile lvs.v file for LVS

  lvs.extend_inputs( ['glb_tile.lvs.v'] )

  # Need sram spice file for LVS

  lvs.extend_inputs( ['sram.spi'] )


  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info           )
  g.add_step( rtl            )
  g.add_step( glb_tile       )
  g.add_step( constraints    )
  g.add_step( dc             )
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
  g.add_step( genlibdb       )
  g.add_step( gdsmerge       )
  g.add_step( drc            )
  g.add_step( lvs            )
  g.add_step( custom_lvs     )
  g.add_step( debugcalibre   )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( adk,      dc             )
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
  g.connect_by_name( adk,      gdsmerge       )
  g.connect_by_name( adk,      drc            )
  g.connect_by_name( adk,      lvs            )

  g.connect_by_name( glb_tile,      dc           )
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
  g.connect_by_name( glb_tile,      genlibdb     )
  g.connect_by_name( glb_tile,      gdsmerge     )
  g.connect_by_name( glb_tile,      drc          )
  g.connect_by_name( glb_tile,      lvs          )

  g.connect_by_name( rtl,         dc        )
  g.connect_by_name( constraints, dc        )

  g.connect_by_name( dc,       iflow        )
  g.connect_by_name( dc,       init         )
  g.connect_by_name( dc,       power        )
  g.connect_by_name( dc,       place        )
  g.connect_by_name( dc,       cts          )

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
  g.connect_by_name( signoff,      gdsmerge       )
  g.connect_by_name( signoff,      drc            )
  g.connect_by_name( signoff,      lvs            )
  g.connect_by_name( gdsmerge,     drc            )
  g.connect_by_name( gdsmerge,     lvs            )

  g.connect_by_name( adk,          pt_signoff     )
  g.connect_by_name( signoff,      pt_signoff     )

  g.connect_by_name( adk,          genlibdb   )
  g.connect_by_name( signoff,      genlibdb   )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( dc,       debugcalibre )
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

  order = init.get_param('order') # get the default script run order
  reporting_idx = order.index( 'reporting.tcl' ) # find reporting.tcl
  # Add dont-touch before reporting
  order.insert ( reporting_idx, 'dont-touch.tcl' )
  init.update_params( { 'order': order } )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


