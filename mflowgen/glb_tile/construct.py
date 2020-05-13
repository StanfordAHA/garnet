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
    'clock_period'   : 1.0,
    'adk'            : adk_name,
    'adk_view'       : adk_view,
    # Synthesis
    'flatten_effort' : 3,
    'topographical'  : True,
    # Floorplan
    'bank_height'    : 8,
    # SRAM macros
    'num_words'      : 2048,
    'word_size'      : 64,
    'mux_size'       : 8,
    'corner'         : "tt0p8v25c",
    'partial_write'  : True,
     # Power Domains
    'PWR_AWARE'         : False,
    # hold target slack
    'hold_target_slack' : 0.050

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
  custom_lvs   = Step( this_dir + '/custom-lvs-rules' )

  # Default steps

  info              = Step( 'info',                          default=True )
  #constraints       = Step( 'constraints',                   default=True )
  dc                = Step( 'synopsys-dc-synthesis',         default=True )
  iflow             = Step( 'cadence-innovus-flowsetup',     default=True )
  init              = Step( 'cadence-innovus-init',          default=True )
  power             = Step( 'cadence-innovus-power',         default=True )
  place             = Step( 'cadence-innovus-place',         default=True )
  cts               = Step( 'cadence-innovus-cts',           default=True )
  postcts_hold      = Step( 'cadence-innovus-postcts_hold',  default=True )
  route             = Step( 'cadence-innovus-route',         default=True )
  postroute         = Step( 'cadence-innovus-postroute',     default=True )
  postroute_hold    = Step( 'cadence-innovus-postroute_hold',default=True )
  signoff           = Step( 'cadence-innovus-signoff',       default=True )
  pt_signoff        = Step( 'synopsys-pt-timing-signoff',    default=True )
  genlibdb          = Step( 'synopsys-ptpx-genlibdb',        default=True )
  gdsmerge          = Step( 'mentor-calibre-gdsmerge',       default=True )
  drc               = Step( 'mentor-calibre-drc',            default=True )
  lvs               = Step( 'mentor-calibre-lvs',            default=True )
  debugcalibre      = Step( 'cadence-innovus-debug-calibre', default=True )

  # Add (dummy) parameters to the default innovus init step

  init.update_params( {
    'core_width'  : 0,
    'core_height' : 0
    }, allow_new=True )

  # Add sram macro inputs to downstream nodes

  dc.extend_inputs( ['sram_tt.db'] )
  pt_signoff.extend_inputs( ['sram_tt.db'] )
  genlibdb.extend_inputs( ['sram_tt.db'] )

  # These steps need timing and lef info for srams

  sram_steps = \
    [iflow, init, power, place, cts, postcts_hold, \
     route, postroute, postroute_hold, signoff]
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

  g.add_step( info           )
  g.add_step( rtl            )
  g.add_step( gen_sram       )
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

  g.connect_by_name( gen_sram,      dc             )
  g.connect_by_name( gen_sram,      iflow          )
  g.connect_by_name( gen_sram,      init           )
  g.connect_by_name( gen_sram,      power          )
  g.connect_by_name( gen_sram,      place          )
  g.connect_by_name( gen_sram,      cts            )
  g.connect_by_name( gen_sram,      postcts_hold   )
  g.connect_by_name( gen_sram,      route          )
  g.connect_by_name( gen_sram,      postroute      )
  g.connect_by_name( gen_sram,      postroute_hold )
  g.connect_by_name( gen_sram,      signoff        )
  g.connect_by_name( gen_sram,      genlibdb       )
  g.connect_by_name( gen_sram,      pt_signoff     )
  g.connect_by_name( gen_sram,      gdsmerge       )
  g.connect_by_name( gen_sram,      drc            )
  g.connect_by_name( gen_sram,      lvs            )

  g.connect_by_name( rtl,         dc        )
  g.connect_by_name( constraints, dc        )

  g.connect_by_name( dc,       iflow        )
  g.connect_by_name( dc,       init         )
  g.connect_by_name( dc,       power        )
  g.connect_by_name( dc,       place        )
  g.connect_by_name( dc,       cts          )

  g.connect_by_name( iflow,    init           )
  g.connect_by_name( iflow,    power          )
  g.connect_by_name( iflow,    place          )
  g.connect_by_name( iflow,    cts            )
  g.connect_by_name( iflow,    postcts_hold   )
  g.connect_by_name( iflow,    route          )
  g.connect_by_name( iflow,    postroute_hold )
  g.connect_by_name( iflow,    postroute      )
  g.connect_by_name( iflow,    signoff        )

  g.connect_by_name( custom_init,  init       )
  g.connect_by_name( custom_power, power      )
  g.connect_by_name( custom_lvs,   lvs        )

  g.connect_by_name( init,           power          )
  g.connect_by_name( power,          place          )
  g.connect_by_name( place,          cts            )
  g.connect_by_name( cts,            postcts_hold   )
  g.connect_by_name( postcts_hold,   route          )
  g.connect_by_name( route,          postroute      )
  g.connect_by_name( postroute,      postroute_hold )
  g.connect_by_name( postroute_hold, signoff        )
  g.connect_by_name( signoff,        gdsmerge       )
  g.connect_by_name( signoff,        drc            )
  g.connect_by_name( signoff,        lvs            )
  g.connect_by_name( gdsmerge,       drc            )
  g.connect_by_name( gdsmerge,       lvs            )

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

  # Add bank height param to init
  init.update_params( { 'bank_height': parameters['bank_height'] }, True )

  # init -- Add 'edge-blockages.tcl' after 'pin-assignments.tcl'

  order = init.get_param('order') # get the default script run order
  pin_idx = order.index( 'pin-assignments.tcl' ) # find pin-assignments.tcl
  order.insert( pin_idx + 1, 'edge-blockages.tcl' ) # add here
  init.update_params( { 'order': order } )

  # Disable pwr aware flow
  init.update_params( { 'PWR_AWARE': parameters['PWR_AWARE'] }, allow_new=True )
  power.update_params( { 'PWR_AWARE': parameters['PWR_AWARE'] }, allow_new=True  )

  # Increase hold slack on postroute_hold step
  postroute_hold.update_params( { 'hold_target_slack': parameters['hold_target_slack'] }, allow_new=True  )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


