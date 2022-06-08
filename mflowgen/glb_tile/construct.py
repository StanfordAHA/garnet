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

  adk_name = get_sys_adk()
  adk_view = 'view-standard'

  parameters = {
    'construct_path' : __file__,
    'design_name'    : 'glb_tile',
    'clock_period'   : 1.11,
    'adk'            : adk_name,
    'adk_view'       : adk_view,
    # Synthesis
    'flatten_effort' : 3,
    'topographical'  : True,
    # Floorplan
    'bank_height'    : 8,
    'array_width' : 32,
    'num_glb_tiles'       : 16,
    # Memory size (unit: KB)
    'glb_tile_mem_size' : 256,
    # SRAM macros
    'num_words'      : 2048,
    'word_size'      : 64,
    'mux_size'       : 8,
    'corner'         : "tt0p8v25c",
    'partial_write'  : True,
     # Power Domains
    'PWR_AWARE'         : False,
    # hold target slack
    'hold_target_slack' : 0.03

  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl          = Step( this_dir + '/../common/rtl'                          )
  constraints  = Step( this_dir + '/constraints'                  )
  gen_sram     = Step( this_dir + '/../common/gen_sram_macro'     )
  custom_init  = Step( this_dir + '/custom-init'                  )
  custom_power = Step( this_dir + '/../common/custom-power-leaf'  )
  short_fix    = Step( this_dir + '/../common/custom-short-fix'   )
  custom_lvs   = Step( this_dir + '/custom-lvs-rules'             )
  genlib       = Step( this_dir + '/../common/cadence-innovus-genlib'    )
  lib2db       = Step( this_dir + '/../common/synopsys-dc-lib2db'        )


  # Default steps

  info              = Step( 'info',                          default=True )
  # constraints       = Step( 'constraints',                   default=True )
  synth             = Step( 'cadence-genus-synthesis',       default=True )
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
  if which("calibre") is not None:
      drc               = Step( 'mentor-calibre-drc',            default=True )
      lvs               = Step( 'mentor-calibre-lvs',            default=True )
  else:
      drc               = Step( 'cadence-pegasus-drc',           default=True )
      lvs               = Step( 'cadence-pegasus-lvs',           default=True )
  debugcalibre      = Step( 'cadence-innovus-debug-calibre', default=True )

  # Add (dummy) parameters to the default innovus init step

  init.update_params( {
    'core_width'  : 0,
    'core_height' : 0
    }, allow_new=True )

  # Add sram macro inputs to downstream nodes

  pt_signoff.extend_inputs( ['sram_tt.db'] )

  # These steps need timing and lef info for srams
  sram_steps = \
    [synth, iflow, init, power, place, cts, postcts_hold, \
     route, postroute, postroute_hold, signoff, genlib]
  for step in sram_steps:
    step.extend_inputs( ['sram_tt.lib', 'sram.lef'] )

  # Need the sram gds to merge into the final layout

  signoff.extend_inputs( ['sram.gds'] )

  # Need SRAM spice file for LVS
  lvs.extend_inputs( ['sram.spi'] )

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  # Add header files to outputs
  rtl.extend_outputs( ['header'] )
  rtl.extend_postconditions( ["assert File( 'outputs/header' ) "] )

  #-----------------------------------------------------------------------
  # Add short_fix script(s) to list of available postroute_hold scripts
  #-----------------------------------------------------------------------

  postroute_hold.extend_inputs( short_fix.all_outputs() )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info           )
  g.add_step( rtl            )
  g.add_step( gen_sram       )
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
  g.add_step( short_fix      )
  g.add_step( postroute_hold )
  g.add_step( signoff        )
  g.add_step( pt_signoff     )
  g.add_step( genlib         )
  g.add_step( lib2db       )
  g.add_step( drc            )
  g.add_step( lvs            )
  g.add_step( custom_lvs     )
  g.add_step( debugcalibre   )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( adk,      gen_sram       )
  g.connect_by_name( adk,      synth          )
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
  g.connect_by_name( adk,      genlib         )

  g.connect_by_name( gen_sram,      synth          )
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
  g.connect_by_name( gen_sram,      genlib         )
  g.connect_by_name( gen_sram,      pt_signoff     )
  g.connect_by_name( gen_sram,      drc            )
  g.connect_by_name( gen_sram,      lvs            )

  g.connect_by_name( rtl,         synth        )
  g.connect_by_name( constraints, synth        )

  g.connect_by_name( synth,       iflow        )
  g.connect_by_name( synth,       init         )
  g.connect_by_name( synth,       power        )
  g.connect_by_name( synth,       place        )
  g.connect_by_name( synth,       cts          )

  g.connect_by_name( iflow,    init           )
  g.connect_by_name( iflow,    power          )
  g.connect_by_name( iflow,    place          )
  g.connect_by_name( iflow,    cts            )
  g.connect_by_name( iflow,    postcts_hold   )
  g.connect_by_name( iflow,    route          )
  g.connect_by_name( iflow,    postroute_hold )
  g.connect_by_name( iflow,    postroute      )
  g.connect_by_name( iflow,    signoff        )
  g.connect_by_name( iflow,    genlib         )

  # Fetch short-fix script in prep for eventual use by postroute_hold
  g.connect_by_name( short_fix, postroute_hold )

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
  g.connect_by_name( signoff,        drc            )
  g.connect_by_name( signoff,        lvs            )
  g.connect(signoff.o('design-merged.gds'), drc.i('design_merged.gds'))
  g.connect(signoff.o('design-merged.gds'), lvs.i('design_merged.gds'))

  g.connect_by_name( signoff, genlib )
  g.connect_by_name( adk,     genlib )

  g.connect_by_name( genlib,     lib2db )

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( synth,    debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( drc,      debugcalibre )
  g.connect_by_name( lvs,      debugcalibre )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  rtl.update_params( { 'glb_only': True }, allow_new=True )

  g.update_params( parameters )

  # Add bank height param to init
  init.update_params( { 'bank_height': parameters['bank_height'] }, True )

  # Change nthreads
  synth.update_params( { 'nthreads': 4 } )
  iflow.update_params( { 'nthreads': 8 } )

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

  # Add fix-shorts as the last thing to do in postroute_hold
  order = postroute_hold.get_param('order') ; # get the default script run order
  order.append('fix-shorts.tcl' )           ; # Add fix-shorts at the end
  postroute_hold.update_params( { 'order': order } ) ; # Update

  # useful_skew
  cts.update_params( { 'useful_skew': False }, allow_new=True )
  # cts.update_params( { 'useful_skew_ccopt_effort': 'extreme' }, allow_new=True )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


