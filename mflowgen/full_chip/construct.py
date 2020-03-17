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
    'construct_path'    : __file__,
    'design_name'       : 'GarnetSOC_pad_frame',
    'clock_period'      : 100.0,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    # Synthesis
    'flatten_effort'    : 3,
    'topographical'     : False,
    # RTL Generation
    'array_width'       : 4,
    'array_height'      : 2,
    'interconnect_only' : False,
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl          = Step( this_dir + '/../common/rtl'                       )
  constraints  = Step( this_dir + '/constraints'                         )
  custom_init  = Step( this_dir + '/custom-init'                         )
  custom_lvs   = Step( this_dir + '/custom-lvs-rules'                    )
  custom_power = Step( this_dir + '/../common/custom-power-hierarchical' )
  dc           = Step( this_dir + '/custom-dc-synthesis'                  )

  # Block-level designs

  tile_array        = Step( this_dir + '/tile_array'        )
  glb_top           = Step( this_dir + '/glb_top'           )
  global_controller = Step( this_dir + '/global_controller' )

  # Default steps

  info         = Step( 'info',                          default=True )
  #constraints  = Step( 'constraints',                   default=True )
  #dc           = Step( 'synopsys-dc-synthesis',         default=True )
  iflow        = Step( 'cadence-innovus-flowsetup',     default=True )
  init         = Step( 'cadence-innovus-init',          default=True )
  power        = Step( 'cadence-innovus-power',         default=True )
  place        = Step( 'cadence-innovus-place',         default=True )
  cts          = Step( 'cadence-innovus-cts',           default=True )
  postcts_hold = Step( 'cadence-innovus-postcts_hold',  default=True )
  route        = Step( 'cadence-innovus-route',         default=True )
  postroute    = Step( 'cadence-innovus-postroute',     default=True )
  signoff      = Step( 'cadence-innovus-signoff',       default=True )
  pt_signoff   = Step( 'synopsys-pt-timing-signoff',    default=True )
  gdsmerge     = Step( 'mentor-calibre-gdsmerge',       default=True )
  drc          = Step( 'mentor-calibre-drc',            default=True )
  lvs          = Step( 'mentor-calibre-lvs',            default=True )
  debugcalibre = Step( 'cadence-innovus-debug-calibre', default=True )

  # Add cgra tile macro inputs to downstream nodes

  dc.extend_inputs( ['tile_array.db'] )
  dc.extend_inputs( ['glb_top.db'] )
  dc.extend_inputs( ['global_controller.db'] )
  pt_signoff.extend_inputs( ['tile_array.db'] )
  pt_signoff.extend_inputs( ['glb_top.db'] )
  pt_signoff.extend_inputs( ['global_controller.db'] )

  # These steps need timing info for cgra tiles

  hier_steps = \
    [ iflow, init, power, place, cts, postcts_hold,
      route, postroute, signoff, gdsmerge ]

  for step in hier_steps:
    step.extend_inputs( ['tile_array_tt.lib', 'tile_array.lef'] )
    step.extend_inputs( ['glb_top_tt.lib', 'glb_top.lef'] )
    step.extend_inputs( ['global_controller_tt.lib', 'global_controller.lef'] )

  # Need the cgra tile gds's to merge into the final layout

  gdsmerge.extend_inputs( ['tile_array.gds'] )
  gdsmerge.extend_inputs( ['glb_top.gds'] )
  gdsmerge.extend_inputs( ['global_controller.gds'] )

  # Need extracted spice files for both tile types to do LVS

  lvs.extend_inputs( ['tile_array.schematic.spi'] )
  lvs.extend_inputs( ['glb_top.schematic.spi'] )
  lvs.extend_inputs( ['global_controller.schematic.spi'] )

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info              )
  g.add_step( rtl               )
  g.add_step( tile_array        )
  g.add_step( glb_top           )
  g.add_step( global_controller )
  g.add_step( constraints       )
  g.add_step( dc                )
  g.add_step( iflow             )
  g.add_step( init              )
  g.add_step( custom_init       )
  g.add_step( power             )
  g.add_step( custom_power      )
  g.add_step( place             )
  g.add_step( cts               )
  g.add_step( postcts_hold      )
  g.add_step( route             )
  g.add_step( postroute         )
  g.add_step( signoff           )
  g.add_step( pt_signoff        )
  g.add_step( gdsmerge          )
  g.add_step( drc               )
  g.add_step( lvs               )
  g.add_step( custom_lvs        )
  g.add_step( debugcalibre      )

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

  # All of the blocks within this hierarchical design
  blocks = [tile_array, glb_top, global_controller]
  for block in blocks:
      g.connect_by_name( block,      dc           )
      g.connect_by_name( block,      iflow        )
      g.connect_by_name( block,      init         )
      g.connect_by_name( block,      power        )
      g.connect_by_name( block,      place        )
      g.connect_by_name( block,      cts          )
      g.connect_by_name( block,      postcts_hold )
      g.connect_by_name( block,      route        )
      g.connect_by_name( block,      postroute    )
      g.connect_by_name( block,      signoff      )
      g.connect_by_name( block,      pt_signoff   )
      g.connect_by_name( block,      gdsmerge     )
      g.connect_by_name( block,      drc          )
      g.connect_by_name( block,      lvs          )

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
  g.connect_by_name( custom_lvs,   lvs      )
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

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )

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

  # init -- Add 'add-endcaps-welltaps.tcl' after 'floorplan.tcl'

  order = init.get_param('order') # get the default script run order
  floorplan_idx = order.index( 'floorplan.tcl' ) # find floorplan.tcl
  order.insert( floorplan_idx + 1, 'add-endcaps-welltaps.tcl' ) # add here
  reporting_idx = order.index( 'reporting.tcl' ) # find reporting.tcl
  # Add dont-touch before reporting
  order.insert ( reporting_idx, 'dont-touch.tcl' )
  init.update_params( { 'order': order } )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


