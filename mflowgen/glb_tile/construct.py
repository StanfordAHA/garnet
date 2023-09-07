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

  adk_name = get_sys_adk()  # E.g. 'gf12-adk' or 'tsmc16'
  adk_view = 'multivt'
  which_soc = 'onyx-intel16'

  parameters = {
    'construct_path'     : __file__,
    'design_name'        : 'glb_tile',
    'clock_period'       : 1.10 * 1000,
    'adk'                : adk_name,
    'adk_view'           : adk_view,
    'adk_stdcell'        : 'b15_7t_108pp',
    # Synthesis
    'flatten_effort'     : 3,
    'topographical'      : True,
    # Floorplan
    'array_width'        : 32,
    'num_glb_tiles'      : 16,
    # Memory size (unit: KB)
    'glb_tile_mem_size'  : 256,
    # SRAM macros
    'num_words'          : 4096,
    'word_size'          : 64,
    'mux_size'           : 4,
    'num_subarrays'      : 2,
    'partial_write'      : True,
    # hold target slack
    'hold_target_slack'  : 0.03,
    'setup_target_slack' : 0.00,
    'drc_env_setup'      : 'drcenv-block.sh'
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps
  # rtl                = Step( this_dir + '/../common/rtl'                          )
  rtl                  = Step( this_dir + '/../common/rtl-cache'                    )
  constraints          = Step( this_dir + '/constraints'                            )
  custom_init          = Step( this_dir + '/custom-init'                            )
  gen_sram             = Step( this_dir + '/../common/gen_sram_macro'               )
  custom_power         = Step( this_dir + '/../common/custom-power-leaf'            )
  custom_lvs           = Step( this_dir + '/custom-lvs-rules'                       )
  lib2db               = Step( this_dir + '/../common/synopsys-dc-lib2db'           )
  custom_cts           = Step( this_dir + '/../common/custom-cts'                   )
  custom_flowgen_setup = Step( this_dir + '/custom-flowgen-setup'                   )
  drc                  = Step( this_dir + '/../common/intel16-synopsys-icv-drc'     )
  lvs                  = Step( this_dir + '/../common/intel16-synopsys-icv-lvs'     )
  # calibre_drc        = Step( this_dir + '/../common/intel16-mentor-calibre-drc'   )
  # calibre_lvs        = Step( this_dir + '/../common/intel16-mentor-calibre-lvs'   )

  # Default steps
  info              = Step( 'info',                          default=True )
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
  genlib            = Step( 'synopsys-ptpx-genlibdb',        default=True )
  debugcalibre      = Step( 'cadence-innovus-debug-calibre', default=True )

  # Add (dummy) parameters to the default innovus init step

  init.update_params( {
    'core_width'  : 0,
    'core_height' : 0
    }, allow_new=True )

  # Add graph inputs and outputs so this can be used in hierarchical flows

  # Inputs
  g.add_input( 'design.v', rtl.i('design.v') )
  g.add_input( 'header'  , rtl.i('header')   )

  # Outputs
  g.add_output( 'glb_tile_tt.lib',      genlib.o('design.lib')         )
  g.add_output( 'glb_tile_tt.db',       lib2db.o('design.db')          )
  g.add_output( 'glb_tile.lef',         signoff.o('design.lef')        )
  g.add_output( 'glb_tile.gds',         signoff.o('design-merged.gds') )
  g.add_output( 'glb_tile.sdf',         signoff.o('design.sdf')        )
  g.add_output( 'glb_tile.vcs.v',       signoff.o('design.vcs.v')      )
  g.add_output( 'glb_tile.vcs.pg.v',    signoff.o('design.vcs.pg.v')   )
  g.add_output( 'glb_tile.spef.gz',     signoff.o('design.spef.gz')    )
  g.add_output( 'glb_tile.lvs.v',       lvs.o('design_merged.lvs.v')   )
  g.add_output( 'glb_tile_sram.spi',    gen_sram.o('sram.spi')         )
  g.add_output( 'glb_tile_sram.v',      gen_sram.o('sram.v')           )
  g.add_output( 'glb_tile_sram_pwr.v',  gen_sram.o('sram_pwr.v')       )
  g.add_output( 'glb_tile_sram_tt.db',  gen_sram.o('sram_tt.db')       )
  g.add_output( 'glb_tile_sram_tt.lib', gen_sram.o('sram_tt.lib')      )
  g.add_output( 'glb_tile_sram_ff.lib', gen_sram.o('sram_ff.lib')      )

  # Add sram macro inputs to downstream nodes
  # [TODO]: Need to do timing signoff/lib gen for 3 different corners (typical, bc, wc)
  genlib.extend_inputs(     ['sram-typical.lib', 'sram-bc.lib', 'sram-wc.lib'] )
  pt_signoff.extend_inputs( ['sram-typical.db',  'sram-bc.db',  'sram-wc.db'] )

  iflow.extend_inputs( custom_flowgen_setup.all_outputs() )

  # These steps need timing and lef info for srams
  sram_steps = \
    [synth, iflow, init, power, place, cts, postcts_hold, \
     route, postroute, postroute_hold, signoff, genlib]
  for step in sram_steps:
    step.extend_inputs( ['sram-typical.lib', 'sram-bc.lib', 'sram-wc.lib', 'sram.lef'] )

  # Need the sram gds/oasis to merge into the final layout
  signoff.extend_inputs( ['sram.gds'] )
  signoff.extend_inputs( ['sram.oas'] )

  # Need SRAM spice file for LVS
  lvs.extend_inputs( ['sram.spi'] )
  calibre_lvs.extend_inputs( ['sram.spi'] )

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )
  cts.extend_inputs( custom_cts.all_outputs() )

  # Header files required for glb rtl output
  rtl.extend_postconditions( ["assert File( 'outputs/header' ) "] )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info                 )
  g.add_step( rtl                  )
  g.add_step( gen_sram             )
  g.add_step( constraints          )
  g.add_step( synth                )
  g.add_step( iflow                )
  g.add_step( init                 )
  g.add_step( custom_init          )
  g.add_step( power                )
  g.add_step( custom_power         )
  g.add_step( place                )
  g.add_step( custom_cts           )
  g.add_step( cts                  )
  g.add_step( postcts_hold         )
  g.add_step( route                )
  g.add_step( postroute            )
  g.add_step( postroute_hold       )
  g.add_step( signoff              )
  g.add_step( pt_signoff           )
  g.add_step( genlib               )
  g.add_step( lib2db               )
  g.add_step( drc                  )
  g.add_step( calibre_drc          )
  g.add_step( lvs                  )
  g.add_step( calibre_lvs          )
  g.add_step( custom_lvs           )
  g.add_step( debugcalibre         )
  g.add_step( custom_flowgen_setup )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name
  g.connect_by_name( adk,                  gen_sram       )
  g.connect_by_name( adk,                  synth          )
  g.connect_by_name( adk,                  iflow          )
  g.connect_by_name( adk,                  init           )
  g.connect_by_name( adk,                  power          )
  g.connect_by_name( adk,                  place          )
  g.connect_by_name( adk,                  cts            )
  g.connect_by_name( adk,                  postcts_hold   )
  g.connect_by_name( adk,                  route          )
  g.connect_by_name( adk,                  postroute      )
  g.connect_by_name( adk,                  postroute_hold )
  g.connect_by_name( adk,                  signoff        )
  g.connect_by_name( adk,                  drc            )
  g.connect_by_name( adk,                  calibre_drc    )
  g.connect_by_name( adk,                  lvs            )
  g.connect_by_name( adk,                  calibre_lvs    )
  g.connect_by_name( adk,                  genlib         )
  g.connect_by_name( gen_sram,             synth          )
  g.connect_by_name( gen_sram,             iflow          )
  g.connect_by_name( gen_sram,             init           )
  g.connect_by_name( gen_sram,             power          )
  g.connect_by_name( gen_sram,             place          )
  g.connect_by_name( gen_sram,             cts            )
  g.connect_by_name( gen_sram,             postcts_hold   )
  g.connect_by_name( gen_sram,             route          )
  g.connect_by_name( gen_sram,             postroute      )
  g.connect_by_name( gen_sram,             postroute_hold )
  g.connect_by_name( gen_sram,             signoff        )
  g.connect_by_name( gen_sram,             genlib         )
  g.connect_by_name( gen_sram,             pt_signoff     )
  g.connect_by_name( gen_sram,             drc            )
  g.connect_by_name( gen_sram,             calibre_drc    )
  g.connect_by_name( gen_sram,             lvs            )
  g.connect_by_name( gen_sram,             calibre_lvs    )
  g.connect_by_name( rtl,                  synth          )
  g.connect_by_name( constraints,          synth          )
  g.connect_by_name( synth,                iflow          )
  g.connect_by_name( synth,                init           )
  g.connect_by_name( synth,                power          )
  g.connect_by_name( synth,                place          )
  g.connect_by_name( synth,                cts            )
  g.connect_by_name( custom_flowgen_setup, iflow          )
  g.connect_by_name( iflow,                init           )
  g.connect_by_name( iflow,                power          )
  g.connect_by_name( iflow,                place          )
  g.connect_by_name( iflow,                cts            )
  g.connect_by_name( iflow,                postcts_hold   )
  g.connect_by_name( iflow,                route          )
  g.connect_by_name( iflow,                postroute_hold )
  g.connect_by_name( iflow,                postroute      )
  g.connect_by_name( iflow,                signoff        )
  g.connect_by_name( iflow,                genlib         )
  g.connect_by_name( custom_init,          init           )
  g.connect_by_name( custom_power,         power          )
  g.connect_by_name( init,                 power          )
  g.connect_by_name( power,                place          )
  g.connect_by_name( place,                cts            )
  g.connect_by_name( cts,                  postcts_hold   )
  g.connect_by_name( postcts_hold,         route          )
  g.connect_by_name( route,                postroute      )
  g.connect_by_name( postroute,            postroute_hold )
  g.connect_by_name( postroute_hold,       signoff        )
  g.connect_by_name( signoff,              drc            )
  g.connect_by_name( signoff,              calibre_drc    )
  g.connect_by_name( signoff,              lvs            )
  g.connect_by_name( signoff,              calibre_lvs    )
  g.connect_by_name( signoff,              genlib         )
  g.connect_by_name( adk,                  genlib         )
  g.connect_by_name( genlib,               lib2db         )
  g.connect_by_name( adk,                  pt_signoff     )
  g.connect_by_name( signoff,              pt_signoff     )
  g.connect_by_name( adk,                  debugcalibre   )
  g.connect_by_name( synth,                debugcalibre   )
  g.connect_by_name( iflow,                debugcalibre   )
  g.connect_by_name( signoff,              debugcalibre   )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  rtl.update_params( { 'glb_only': True }, allow_new=True )

  g.update_params( parameters )

  # Add bank height param to init
  # number of banks is fixed to 2
  bank_height = (parameters['glb_tile_mem_size'] * 1024 // 2) // (parameters['num_words'] * (parameters['word_size'] // 8))
  init.update_params( { 'bank_height': bank_height }, True )

  # Change nthreads
  synth.update_params( { 'nthreads': 4 } )
  iflow.update_params( { 'nthreads': 8 } )

  # init -- Add 'edge-blockages.tcl' after 'pin-assignments.tcl'
  init.update_params( { 'order': [
    'pre-init.tcl',
    'main.tcl',
    'innovus-pnr-config.tcl',
    'dont-use.tcl',
    'quality-of-life.tcl',
    'floorplan.tcl',
    'pin-assignments.tcl',
    'create-rows.tcl',
    'add-tracks.tcl',
    'create-boundary-blockage.tcl',
    'add-endcaps-welltaps.tcl',
    'insert-input-antenna-diodes.tcl',
    'create-special-grid.tcl',
    'make-path-groups.tcl',
    'reporting.tcl'
  ] } )

  # Increase hold slack on postroute_hold step
  postroute_hold.update_params( { 'hold_target_slack': parameters['hold_target_slack'] }, allow_new=True  )

  # Add fix-shorts as the last thing to do in postroute_hold
  # order = postroute_hold.get_param('order') ; # get the default script run order
  # order.append('fix-shorts.tcl' )           ; # Add fix-shorts at the end
  # postroute_hold.update_params( { 'order': order } ) ; # Update

  # useful_skew
  cts.update_params( { 'useful_skew': False }, allow_new=True )
  # cts.update_params( { 'useful_skew_ccopt_effort': 'extreme' }, allow_new=True )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


