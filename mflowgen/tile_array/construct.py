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
    'design_name'    : 'Interconnect',
    'clock_period'   : 10.0,
    'adk'            : adk_name,
    'adk_view'       : adk_view,
    # Synthesis
    'flatten_effort' : 3,
    'topographical'  : False,
    # Floorplan
    'core_width'     : 3000.0,
    'core_height'    : 2200.0,
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl          = Step( this_dir + '/../common/rtl'           )
  Tile_MemCore = Step( this_dir + '/Tile_MemCore'            )
  Tile_PE      = Step( this_dir + '/Tile_PE'                 )
  constraints  = Step( this_dir + '/constraints'             )
  custom_init  = Step( this_dir + '/custom-init'             )
  custom_power = Step( this_dir + '/custom-power'            )

  # Default steps

  info         = Step( 'info',                          default=True )
  #constraints  = Step( 'constraints',                   default=True )
  dc           = Step( 'synopsys-dc-synthesis',         default=True )
  iflow        = Step( 'cadence-innovus-flowsetup',     default=True )
  init         = Step( 'cadence-innovus-init',          default=True )
  power        = Step( 'cadence-innovus-power',         default=True )
  place        = Step( 'cadence-innovus-place',         default=True )
  cts          = Step( 'cadence-innovus-cts',           default=True )
  postcts_hold = Step( 'cadence-innovus-postcts_hold',  default=True )
  route        = Step( 'cadence-innovus-route',         default=True )
  postroute    = Step( 'cadence-innovus-postroute',     default=True )
  signoff      = Step( 'cadence-innovus-signoff',       default=True )
  gdsmerge     = Step( 'mentor-calibre-gdsmerge',       default=True )
  drc          = Step( 'mentor-calibre-drc',            default=True )
  lvs          = Step( 'mentor-calibre-lvs',            default=True )
  debugcalibre = Step( 'cadence-innovus-debug-calibre', default=True )

  # Add (dummy) parameters to the default innovus init step

  init.update_params( {
    'core_width'  : 0,
    'core_height' : 0
    }, allow_new=True )

  # Add cgra tile macro inputs to downstream nodes

  dc.extend_inputs( ['Tile_PE.db'] )
  dc.extend_inputs( ['Tile_MemCore.db'] )

  # These steps need timing info for cgra tiles

  tile_steps = \
    [ iflow, init, power, place, cts, postcts_hold,
      route, postroute, signoff, gdsmerge ]

  for step in tile_steps:
    step.extend_inputs( ['Tile_PE_tt.lib', 'Tile_PE.lef'] )
    step.extend_inputs( ['Tile_MemCore_tt.lib', 'Tile_MemCore.lef'] )

  # Need the cgra tile gds's to merge into the final layout

  gdsmerge.extend_inputs( ['Tile_PE.gds'] )
  gdsmerge.extend_inputs( ['Tile_MemCore.gds'] )

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info         )
  g.add_step( rtl          )
  g.add_step( Tile_MemCore )
  g.add_step( Tile_PE      )
  g.add_step( constraints  )
  g.add_step( dc           )
  g.add_step( iflow        )
  g.add_step( init         )
  g.add_step( custom_init  )
  g.add_step( power        )
  g.add_step( custom_power )
  g.add_step( place        )
  g.add_step( cts          )
  g.add_step( postcts_hold )
  g.add_step( route        )
  g.add_step( postroute    )
  g.add_step( signoff      )
  g.add_step( gdsmerge     )
  g.add_step( drc          )
  g.add_step( lvs          )
  g.add_step( debugcalibre )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( adk,      dc           )
  g.connect_by_name( adk,      iflow        )
  g.connect_by_name( adk,      init         )
  g.connect_by_name( adk,      power        )
  g.connect_by_name( adk,      place        )
  g.connect_by_name( adk,      cts          )
  g.connect_by_name( adk,      postcts_hold )
  g.connect_by_name( adk,      route        )
  g.connect_by_name( adk,      postroute    )
  g.connect_by_name( adk,      signoff      )
  g.connect_by_name( adk,      gdsmerge     )
  g.connect_by_name( adk,      drc          )
  g.connect_by_name( adk,      lvs          )

  g.connect_by_name( Tile_MemCore,      dc           )
  g.connect_by_name( Tile_MemCore,      iflow        )
  g.connect_by_name( Tile_MemCore,      init         )
  g.connect_by_name( Tile_MemCore,      power        )
  g.connect_by_name( Tile_MemCore,      place        )
  g.connect_by_name( Tile_MemCore,      cts          )
  g.connect_by_name( Tile_MemCore,      postcts_hold )
  g.connect_by_name( Tile_MemCore,      route        )
  g.connect_by_name( Tile_MemCore,      postroute    )
  g.connect_by_name( Tile_MemCore,      signoff      )
  g.connect_by_name( Tile_MemCore,      gdsmerge     )
  g.connect_by_name( Tile_MemCore,      drc          )
  g.connect_by_name( Tile_MemCore,      lvs          )

  g.connect_by_name( Tile_PE,      dc           )
  g.connect_by_name( Tile_PE,      iflow        )
  g.connect_by_name( Tile_PE,      init         )
  g.connect_by_name( Tile_PE,      power        )
  g.connect_by_name( Tile_PE,      place        )
  g.connect_by_name( Tile_PE,      cts          )
  g.connect_by_name( Tile_PE,      postcts_hold )
  g.connect_by_name( Tile_PE,      route        )
  g.connect_by_name( Tile_PE,      postroute    )
  g.connect_by_name( Tile_PE,      signoff      )
  g.connect_by_name( Tile_PE,      gdsmerge     )
  g.connect_by_name( Tile_PE,      drc          )
  g.connect_by_name( Tile_PE,      lvs          )

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
  g.connect_by_name( iflow,    signoff      )

  g.connect_by_name( custom_init,  init     )
  g.connect_by_name( custom_power, power    )

  g.connect_by_name( init,         power        )
  g.connect_by_name( power,        place        )
  g.connect_by_name( place,        cts          )
  g.connect_by_name( cts,          postcts_hold )
  g.connect_by_name( postcts_hold, route        )
  g.connect_by_name( route,        postroute    )
  g.connect_by_name( postroute,    signoff      )
  g.connect_by_name( signoff,      gdsmerge     )
  g.connect_by_name( signoff,      drc          )
  g.connect_by_name( signoff,      lvs          )
  g.connect_by_name( gdsmerge,     drc          )
  g.connect_by_name( gdsmerge,     lvs          )

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
  
  # Since we are adding an additional input to the init node, we must add
  # that input to the order parameter for that node, so it actually gets run
  init.update_params(
                     {'order': "\"main.tcl quality-of-life.tcl floorplan.tcl add-endcaps-welltaps.tcl "\
                               "pin-assignments.tcl make-path-groups.tcl reporting.tcl\""}
                    )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


