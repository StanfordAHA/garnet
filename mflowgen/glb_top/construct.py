#! /usr/bin/env python
#=========================================================================
# construct.py
#=========================================================================
# Author :
# Date   :
#

import os
import sys
import pathlib

from mflowgen.components import Graph, Step, Subgraph
from shutil import which
from common.get_sys_adk import get_sys_adk

def construct():

  g = Graph()

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  adk_name = get_sys_adk()  # E.g. 'gf12-adk' or 'tsmc16'
  adk_view = 'multivt'
  which_soc = 'onyx'

  parameters = {
    'construct_path'      : __file__,
    'design_name'         : 'global_buffer',
    'clock_period'        : 2.0 * 1000,
    'adk'                 : adk_name,
    'adk_view'            : adk_view,
    'adk_stdcell'         : 'b0m_6t_108pp',
    'adk_libmodel'        : 'nldm',
    # Synthesis
    'flatten_effort'      : 3,
    'topographical'       : True,
    # hold target slack
    'hold_target_slack'   : 0.1,
    # array_width = width of CGRA below GLB; `pin-assignments.tcl` uses
    # these parms to set up per-cgra-column ports connecting glb tile
    # signals in glb_top to corresponding CGRA tile columns below glb_top
    'array_width'         : 28,
    'num_glb_tiles'       : 14,
    # glb tile memory size (unit: KB)
    'use_container'       : True,
    'glb_tile_mem_size'   : 128,
    'sdf'                 : True,
    'saif'                : False,
    'waveform'            : True,
    'useful_skew'         : True
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # Initialization orders
  init_order = [
    'pre-init.tcl',
    'main.tcl',
    'innovus-pnr-config.tcl',
    'enable-gmz-routing.tcl',
    'dont-use.tcl',
    'quality-of-life.tcl',
    'floorplan.tcl',
    'create-rows.tcl',
    'add-endcaps-welltaps.tcl',
    'pin-assignments.tcl',
    'add-tracks.tcl',
    'create-boundary-blockage.tcl',
    'insert-input-antenna-diodes.tcl',
    'create-special-grid.tcl',
    'make-path-groups.tcl',
    'dont-touch.tcl',
    'reporting.tcl'
  ]

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()
  
  # Subgraphs

  glb_tile = Subgraph( this_dir + '/../glb_tile', 'glb_tile' )

  # Custom steps
  
  rtl                  = Step( this_dir + '/../common/rtl'                               )
  constraints          = Step( this_dir + '/constraints'                                 )
  custom_init          = Step( this_dir + '/custom-init'                                 )
  custom_power         = Step( this_dir + '/custom-power-hierarchical-glb-top'           )
  custom_cts           = Step( this_dir + '/custom-cts'                                  )
  custom_flowgen_setup = Step( this_dir + '/custom-flowgen-setup'                        )
  drc                  = Step( this_dir + '/../common/intel16-synopsys-icv-drc'          )
  lvs                  = Step( this_dir + '/../common/intel16-synopsys-icv-lvs'          )
  custom_hack_sdc_unit = Step( this_dir + '/../common/custom-hack-sdc-unit'              )
  custom_pre_signoff   = Step( this_dir + '/custom-pre-signoff'                          )

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
  pt_signoff_flat= Step( 'synopsys-pt-timing-signoff-flat', default=True )

  genlibdb_tt       = Step( this_dir + '/../common/cadence-innovus-genlib')
  genlibdb_ff       = Step( this_dir + '/../common/cadence-innovus-genlib')
  genlibdb_tt.set_name( 'cadence-innovus-genlibdb-tt' )
  genlibdb_ff.set_name( 'cadence-innovus-genlibdb-ff' )
  
  # Inputs
  g.add_input( 'design.v', rtl.i('design.v') )
  g.add_input( 'header'  , rtl.i('header')   )

  # Outputs
  g.add_output( 'global_buffer-typical.lib',      genlibdb_tt.o('design.lib')             )
  g.add_output( 'global_buffer-typical.db',       genlibdb_tt.o('design.db')              )
  g.add_output( 'global_buffer-bc.lib',           genlibdb_ff.o('design.lib')             )
  g.add_output( 'global_buffer-bc.db',            genlibdb_ff.o('design.db')              )
  g.add_output( 'global_buffer.lef',              signoff.o('design.lef')                 )
  g.add_output( 'global_buffer.oas',              signoff.o('design-merged.oas')          )
  g.add_output( 'global_buffer.sdf',              signoff.o('design.sdf')                 )
  g.add_output( 'global_buffer.vcs.v',            signoff.o('design.vcs.v')               )
  g.add_output( 'global_buffer.vcs.pg.v',         signoff.o('design.vcs.pg.v')            )
  g.add_output( 'global_buffer.pt.sdc',           signoff.o('design.pt.sdc')              )
  g.add_output( 'global_buffer.spef.gz',          signoff.o('design.spef.gz')             )
  g.add_output( 'global_buffer.rcbest.spef.gz',   signoff.o('design.rcbest.spef.gz')      )
  g.add_output( 'global_buffer.lvs.v',            lvs.o('design_merged.lvs.v')            )
  g.add_output( 'global_buffer_sram.spi',         glb_tile.o('glb_tile_sram.spi')         )
  g.add_output( 'global_buffer_sram.v',           glb_tile.o('glb_tile_sram.v')           )
  g.add_output( 'global_buffer_sram-bc.db',       glb_tile.o('glb_tile_sram-bc.db')       )
  g.add_output( 'global_buffer_sram-bc.lib',      glb_tile.o('glb_tile_sram-bc.lib')      )
  g.add_output( 'global_buffer_sram-wc.db',       glb_tile.o('glb_tile_sram-wc.db')       )
  g.add_output( 'global_buffer_sram-wc.lib',      glb_tile.o('glb_tile_sram-wc.lib')      )
  g.add_output( 'global_buffer_sram-typical.db',  glb_tile.o('glb_tile_sram-typical.db')  )
  g.add_output( 'global_buffer_sram-typical.lib', glb_tile.o('glb_tile_sram-typical.lib') )

  signoff.extend_inputs( custom_pre_signoff.all_outputs() )


  # Add header files to outputs
  rtl.extend_outputs( ['header'] )
  rtl.extend_postconditions( ["assert File( 'outputs/header' ) "] )

  # Add (dummy) parameters to the default innovus init step

  init.update_params( {
    'core_width'  : 0,
    'core_height' : 0
    }, allow_new=True )

  # Add glb_tile macro inputs to downstream nodes

  pt_signoff.extend_inputs( ['glb_tile-typical.db', 'glb_tile-bc.db'] )
  pt_signoff_flat.extend_inputs( ['glb_tile_sram-typical.db', 'glb_tile_sram-bc.db', 'glb_tile.vcs.v', 'glb_tile.pt.sdc', 'glb_tile.spef.gz'] )
  genlibdb_tt.extend_inputs( ['glb_tile-typical.db'] )
  genlibdb_ff.extend_inputs( ['glb_tile-bc.db'] )

  # These steps need timing info for glb_tiles
  tile_steps = \
    [ synth, iflow, init, power, place, cts, postcts_hold,
      route, postroute, postroute_hold, signoff ]

  for step in tile_steps:
    step.extend_inputs( ['glb_tile-typical.lib', 'glb_tile-bc.lib', 'glb_tile.lef'] )

  # Need the glb_tile oasis to merge into the final layout

  signoff.extend_inputs( ['glb_tile.oas'] )

  # Need glb_tile lvs.v file for LVS

  lvs.extend_inputs( ['glb_tile.lvs.v'] )

  # Need sram spice file for LVS
  lvs.extend_inputs( ['glb_tile_sram.spi'] )

  # Add extra input edges to innovus steps that need custom tweaks
  iflow.extend_inputs( custom_flowgen_setup.all_outputs() )
  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )
  cts.extend_inputs( custom_cts.all_outputs() )

  # SDC hack for the genlibdb and pt_signoff steps
  # genlibdb_tt.extend_inputs( custom_hack_sdc_unit.all_outputs() )
  # genlibdb_ff.extend_inputs( custom_hack_sdc_unit.all_outputs() )
  pt_signoff.extend_inputs( custom_hack_sdc_unit.all_outputs() )
  pt_signoff_flat.extend_inputs( custom_hack_sdc_unit.all_outputs() )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info                 )
  g.add_step( rtl                  )
  g.add_step( glb_tile             )
  g.add_step( constraints          )
  g.add_step( synth                )
  g.add_step( custom_flowgen_setup )
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
  g.add_step( pt_signoff_flat      )
  g.add_step( genlibdb_tt          )
  g.add_step( genlibdb_ff          )
  g.add_step( drc                  )
  g.add_step( lvs                  )
  g.add_step( custom_hack_sdc_unit )
  g.add_step( custom_pre_signoff   )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

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
  g.connect_by_name( adk,      genlibdb_tt    )
  g.connect_by_name( adk,      genlibdb_ff    )

  g.connect_by_name( glb_tile,      synth          )
  g.connect_by_name( glb_tile,      iflow          )
  g.connect_by_name( glb_tile,      init           )
  g.connect_by_name( glb_tile,      power          )
  g.connect_by_name( glb_tile,      place          )
  g.connect_by_name( glb_tile,      cts            )
  g.connect_by_name( glb_tile,      postcts_hold   )
  g.connect_by_name( glb_tile,      route          )
  g.connect_by_name( glb_tile,      postroute      )
  g.connect_by_name( glb_tile,      postroute_hold )
  g.connect_by_name( glb_tile,      signoff        )
  g.connect_by_name( glb_tile,      pt_signoff     )
  g.connect_by_name( glb_tile,      pt_signoff_flat)
  g.connect_by_name( glb_tile,      genlibdb_tt    )
  g.connect_by_name( glb_tile,      genlibdb_ff    )
  g.connect_by_name( glb_tile,      drc            )
  g.connect_by_name( glb_tile,      lvs            )

  g.connect_by_name( rtl,         synth        )
  g.connect_by_name( constraints, synth        )

  # glb_tile can use the same rtl as glb_top
  g.connect_by_name( rtl,         glb_tile     )

  g.connect_by_name( synth,       iflow        )
  g.connect_by_name( synth,       init         )
  g.connect_by_name( synth,       power        )
  g.connect_by_name( synth,       place        )
  g.connect_by_name( synth,       cts          )
  
  g.connect_by_name( custom_flowgen_setup,  iflow          )
  g.connect_by_name( iflow,                 init           )
  g.connect_by_name( iflow,                 power          )
  g.connect_by_name( iflow,                 place          )
  g.connect_by_name( iflow,                 cts            )
  g.connect_by_name( iflow,                 postcts_hold   )
  g.connect_by_name( iflow,                 route          )
  g.connect_by_name( iflow,                 postroute      )
  g.connect_by_name( iflow,                 postroute_hold )
  g.connect_by_name( iflow,                 signoff        )
  g.connect_by_name( iflow,                 genlibdb_tt    )
  g.connect_by_name( iflow,                 genlibdb_ff    )


  g.connect_by_name( custom_init,        init    )
  g.connect_by_name( custom_power,       power   )
  g.connect_by_name( custom_pre_signoff, signoff )
  g.connect_by_name( custom_cts,         cts     )

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

  g.connect_by_name( adk,          pt_signoff     )
  g.connect_by_name( signoff,      pt_signoff     )
  g.connect_by_name( adk,          pt_signoff_flat)
  g.connect_by_name( signoff,      pt_signoff_flat)

  g.connect_by_name( signoff,      genlibdb_tt     )
  g.connect_by_name( signoff,      genlibdb_ff     )

  # SDC hack for the genlibdb and pt_signoff steps
  # g.connect_by_name( custom_hack_sdc_unit, genlibdb_tt )
  # g.connect_by_name( custom_hack_sdc_unit, genlibdb_ff )
  g.connect_by_name( custom_hack_sdc_unit, pt_signoff )
  g.connect_by_name( custom_hack_sdc_unit, pt_signoff_flat )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  # Add signoff ECO routing (looks like it's a fake DRC, skip this step)
  order = signoff.get_param( 'order' )
  order = ['pre-signoff.tcl'] + order
  signoff.set_param( 'order', order )

  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

  # rtl parameters update
#  rtl.update_params( { 'glb_only': True }, allow_new=True )

  # pin assignment parameters update
  init.update_params( { 'array_width': parameters['array_width'] }, allow_new=True )
  init.update_params( { 'num_glb_tiles': parameters['num_glb_tiles'] }, allow_new=True )

  # init -- update custom order
  init.update_params( { 'order': init_order } )

  # update clock insertion delay in CTS
  order = cts.get_param( 'order' )
  order.insert(order.index('main.tcl'), 'custom-cts-additional-setup.tcl')
  cts.set_param( 'order', order )

  # DRC Rule Decks
  drc_rule_decks = [
    "antenna",
    "collat",
    "drc-drcd",
    "drc-lu",
    # "drc-denall"
    # "drc-cden-lden-collat",
    # "drc-fullchip",
    # "tapein"
  ]
  drc.update_params( {'rule_decks': drc_rule_decks } )

  # genlibdb parameters
  # genlibdb_order = [
  #   'read_design.tcl',
  #   'extract_model.tcl'
  # ]
  # genlibdb_tt.update_params({
  #   'corner': 'typical',
  #   'order': genlibdb_order
  # })
  # genlibdb_ff.update_params({
  #   'corner': 'bc',
  #   'order': genlibdb_order
  # })
  genlibdb_tt.update_params({'corner': 'typical'})
  genlibdb_ff.update_params({'corner': 'bc'})

  # Add SDC unit hack before genlibdb and pt_signoff
  # The SDC file generated by Innovus contains -library flag to explicitly
  # specify which library to use for the cell. However, we will change the
  # target library for different corners and that makes the SDC commands
  # fail to find the cell. We should remove the -library flag and let the
  # tool find the cell from the target library (default behavior).
  pt_signoff.pre_extend_commands( [
    "python inputs/hack_sdc_unit.py inputs/design.pt.sdc",
    "sed -i 's/-library [^ ]* //g' inputs/design.pt.sdc",
  ] )
  pt_signoff_flat.pre_extend_commands( [
    "python inputs/hack_sdc_unit.py inputs/design.pt.sdc",
    "sed -i 's/-library [^ ]* //g'  inputs/design.pt.sdc",
    "python inputs/hack_sdc_unit.py inputs/glb_tile.pt.sdc",
    "sed -i 's/-library [^ ]* //g'  inputs/glb_tile.pt.sdc",
  ] )

  # Increase hold slack on postroute_hold step
  postroute_hold.update_params( { 'hold_target_slack': parameters['hold_target_slack'] }, allow_new=True  )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


