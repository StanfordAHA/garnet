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
    'design_name'    : 'glb_tile',
    'clock_period'   : 3.0,
    'adk'            : adk_name,
    'adk_view'       : adk_view,
    # Synthesis
    'flatten_effort' : 3,
    'topographical'  : False,
    # Floorplan
    'core_width'     : 350.0,
    'core_height'    : 1900.0,
    # SRAM macros
    'num_words'      : 2048,
    'word_size'      : 64,
    'mux_size'       : 8,
    'corner'         : "tt0p8v25c",
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl          = Step( this_dir + '/rtl'                         )
  constraints  = Step( this_dir + '/constraints'                 )
  gen_sram     = Step( this_dir + '/../common/gen_sram_macro'    )
  custom_init  = Step( this_dir + '/custom-init'                 )
  custom_power = Step( this_dir + '/../common/custom-power-leaf' )

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
  pt_signoff   = Step( 'synopsys-pt-timing-signoff',    default=True )
  genlibdb     = Step( 'synopsys-ptpx-genlibdb',        default=True )
  gdsmerge     = Step( 'mentor-calibre-gdsmerge',       default=True )
  drc          = Step( 'mentor-calibre-drc',            default=True )
  lvs          = Step( 'mentor-calibre-lvs',            default=True )
  debugcalibre = Step( 'cadence-innovus-debug-calibre', default=True )

  # Add (dummy) parameters to the default innovus init step

  init.update_params( {
    'core_width'  : 0,
    'core_height' : 0
    }, allow_new=True )

  # Add sram macro inputs to downstream nodes

  dc.extend_inputs( ['sram_tt.db'] )

  # These steps need timing and lef info for srams

  sram_steps = \
    [iflow, init, power, place, cts, postcts_hold, route, postroute, signoff]
  for step in sram_steps:
    step.extend_inputs( ['sram_tt.lib', 'sram.lef'] )

  # Need the sram gds to merge into the final layout

  gdsmerge.extend_inputs( ['sram.gds'] )

  # Need SRAM spice file for LVS
  lvs.extend_inputs( ['sram.spi'] )

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info         )
  g.add_step( rtl          )
  g.add_step( gen_sram     )
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
  g.add_step( pt_signoff   )
  g.add_step( genlibdb     )
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

  g.connect_by_name( gen_sram,      dc           )
  g.connect_by_name( gen_sram,      iflow        )
  g.connect_by_name( gen_sram,      init         )
  g.connect_by_name( gen_sram,      power        )
  g.connect_by_name( gen_sram,      place        )
  g.connect_by_name( gen_sram,      cts          )
  g.connect_by_name( gen_sram,      postcts_hold )
  g.connect_by_name( gen_sram,      route        )
  g.connect_by_name( gen_sram,      postroute    )
  g.connect_by_name( gen_sram,      signoff      )
  g.connect_by_name( gen_sram,      gdsmerge     )
  g.connect_by_name( gen_sram,      drc          )
  g.connect_by_name( gen_sram,      lvs          )

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

  g.connect_by_name( signoff, genlibdb )
  g.connect_by_name( adk,     genlibdb )

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
  init.update_params( { 'order': order } )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


