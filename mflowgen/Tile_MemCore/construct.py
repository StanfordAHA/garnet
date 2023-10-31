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

  read_hdl_defines = 'INTEL16'

  parameters = {
    'construct_path'      : __file__,
    'design_name'         : 'Tile_MemCore',
    'clock_period'        : 1.10*1000,
    'adk'                 : adk_name,
    'adk_view'            : adk_view,
    'adk_stdcell'         : 'b15_7t_108pp',
    # Synthesis
    'flatten_effort'      : 3,
    'topographical'       : True,
    'read_hdl_defines'    : read_hdl_defines,
    # SRAM macros
    'num_words'           : 512,
    'word_size'           : 32,
    'mux_size'            : 4,
    'partial_write'       : False,
    # Hold target slack
    'setup_target_slack'  : 0,
    'hold_target_slack'   : 0.015,
    # Utilization target
    'core_density_target' : 0.68,
    # RTL Generation
    'interconnect_only'   : False,
    'rtl_docker_image'    : 'default', # Current default is 'stanfordaha/garnet:latest'
    # Power analysis
    "use_sdf"             : False, # uses sdf but not the way it is in xrun node
    'app_to_run'          : 'tests/conv_3_3',
    'saif_instance'       : 'testbench/dut',
    'testbench_name'      : 'testbench',
    'strip_path'          : 'testbench/dut',
    'drc_env_setup'       : 'drcenv-block.sh'
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step
  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps
  rtl                  = Step( this_dir + '/../common/rtl'                          )
  #rtl                  = Step( this_dir + '/../common/rtl-cache'                    )
  genlibdb_constraints = Step( this_dir + '/../common/custom-genlibdb-constraints'  )
  constraints          = Step( this_dir + '/constraints'                            )
  custom_init          = Step( this_dir + '/custom-init'                            )
  custom_genus_scripts = Step( this_dir + '/custom-genus-scripts'                   )
  custom_flowgen_setup = Step( this_dir + '/custom-flowgen-setup'                   )
  custom_cts           = Step( this_dir + '/custom-cts'                             )
  gen_sram             = Step( this_dir + '/../common/gen_sram_macro'               )
  custom_lvs           = Step( this_dir + '/custom-lvs-rules'                       )
  custom_power         = Step( this_dir + '/../common/custom-power-leaf'            )
  testbench            = Step( this_dir + '/../common/testbench'                    )
  application          = Step( this_dir + '/../common/application'                  )
  lib2db               = Step( this_dir + '/../common/synopsys-dc-lib2db'           )

  post_pnr_power       = Step( this_dir + '/../common/tile-post-pnr-power'          )
  drc                  = Step( this_dir + '/../common/intel16-synopsys-icv-drc'     )
  lvs                  = Step( this_dir + '/../common/intel16-synopsys-icv-lvs'     )

  # Default steps
  info                 = Step( 'info',                                 default=True )
  synth                = Step( 'cadence-genus-synthesis',              default=True )
  iflow                = Step( 'cadence-innovus-flowsetup',            default=True )
  init                 = Step( 'cadence-innovus-init',                 default=True )
  power                = Step( 'cadence-innovus-power',                default=True )
  place                = Step( 'cadence-innovus-place',                default=True )
  cts                  = Step( 'cadence-innovus-cts',                  default=True )
  postcts_hold         = Step( 'cadence-innovus-postcts_hold',         default=True )
  route                = Step( 'cadence-innovus-route',                default=True )
  postroute            = Step( 'cadence-innovus-postroute',            default=True )
  postroute_hold       = Step( 'cadence-innovus-postroute_hold',       default=True )
  signoff              = Step( 'cadence-innovus-signoff',              default=True )
  pt_signoff           = Step( 'synopsys-pt-timing-signoff',           default=True )
  genlibdb             = Step( 'synopsys-ptpx-genlibdb',               default=True )
  debugcalibre         = Step( 'cadence-innovus-debug-calibre',        default=True )



  # Extra DC input
  synth.extend_inputs(["common.tcl"])
  synth.extend_inputs(["simple_common.tcl"])

  # Add sram macro inputs to downstream nodes
  synth.extend_inputs(      ['sram-typical.lib', 'sram-bc.lib', 'sram-wc.lib', 'sram.lef'] )
  pt_signoff.extend_inputs( ['sram-typical.db',  'sram-bc.db',  'sram-wc.db'] )
  genlibdb.extend_inputs(   ['sram-typical.db', 'sram-bc.db', 'sram-wc.db'] )


  # These steps need timing and lef info for srams
  sram_steps = \
    [iflow, init, power, place, cts, postcts_hold, route, postroute, postroute_hold, signoff]
  for step in sram_steps:
    step.extend_inputs( ['sram-typical.lib', 'sram-bc.lib', 'sram-wc.lib', 'sram.lef'] )

  # Need the sram oasis to merge into the final layout
  signoff.extend_inputs( ['sram.oas'] )

  # Need SRAM spice file for LVS
  lvs.extend_inputs( ['sram.spi'] )

  # Add extra input edges to innovus steps that need custom tweaks
  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  # Add extra input edges to genlibdb for loop-breaking constraints
  genlibdb.extend_inputs( genlibdb_constraints.all_outputs() )
  synth.extend_inputs( custom_genus_scripts.all_outputs() )
  iflow.extend_inputs( custom_flowgen_setup.all_outputs() )

  synth.extend_outputs( ["sdc"] )
  iflow.extend_inputs( ["sdc"] )
  init.extend_inputs( ["sdc"] )
  power.extend_inputs( ["sdc"] )
  place.extend_inputs( ["sdc"] )
  cts.extend_inputs( ["sdc"] )
  
  # Add graph inputs and outputs so this can be used in hierarchical flows

  # Inputs
  g.add_input( 'design.v', rtl.i('design.v') )
  # Outputs
  g.add_output( 'Tile_MemCore_tt.lib',      genlibdb.o('design.lib')           )
  g.add_output( 'Tile_MemCore_tt.db',       genlibdb.o('design.db')            )
  g.add_output( 'Tile_MemCore.lef',         signoff.o('design.lef')            )
  g.add_output( 'Tile_MemCore.oas',         signoff.o('design-merged.oas')     )
  g.add_output( 'Tile_MemCore.sdf',         signoff.o('design.sdf')            )
  g.add_output( 'Tile_MemCore.vcs.v',       signoff.o('design.vcs.v')          )
  g.add_output( 'Tile_MemCore.vcs.pg.v',    signoff.o('design.vcs.pg.v')       )
  g.add_output( 'Tile_MemCore.spef.gz',     signoff.o('design.rcbest.spef.gz') )
  g.add_output( 'Tile_MemCore.pt.sdc',      signoff.o('design.pt.sdc')         )
  g.add_output( 'Tile_MemCore.lvs.v',       lvs.o('design_merged.lvs.v')       )
  g.add_output( 'sram.spi',                 gen_sram.o('sram.spi')             )
  g.add_output( 'sram.v',                   gen_sram.o('sram.v')               )
  #g.add_output( 'sram_pwr.v',               gen_sram.o('sram_pwr.v')           )
  g.add_output( 'sram_bc.db',               gen_sram.o('sram-bc.db')           )
  g.add_output( 'sram_bc.lib',              gen_sram.o('sram-bc.lib')          )
  g.add_output( 'sram_wc.db',               gen_sram.o('sram-wc.db')           )
  g.add_output( 'sram_wc.lib',              gen_sram.o('sram-wc.lib')          )
  g.add_output( 'sram_typical.db',          gen_sram.o('sram-typical.db')      )
  g.add_output( 'sram_typical.lib',         gen_sram.o('sram-typical.lib')     )

  order = synth.get_param( 'order' )
  order.append( 'copy_sdc.tcl' )
  synth.set_param( 'order', order )

  cts.extend_inputs( custom_cts.all_outputs() )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------
  g.add_step( info                 )
  g.add_step( rtl                  )
  g.add_step( gen_sram             )
  g.add_step( constraints          )
  g.add_step( synth                )
  g.add_step( custom_genus_scripts )
  g.add_step( iflow                )
  g.add_step( custom_flowgen_setup )
  g.add_step( init                 )
  g.add_step( custom_init          )
  g.add_step( power                )
  g.add_step( custom_power         )
  g.add_step( place                )
  g.add_step( cts                  )
  g.add_step( postcts_hold         )
  g.add_step( route                )
  g.add_step( postroute            )
  g.add_step( postroute_hold       )
  g.add_step( signoff              )
  g.add_step( pt_signoff           )
  g.add_step( genlibdb_constraints )
  g.add_step( genlibdb             )
  g.add_step( lib2db               )
  g.add_step( drc                  )
  g.add_step( lvs                  )
  g.add_step( custom_lvs           )
  g.add_step( debugcalibre         )
  g.add_step( application          )
  g.add_step( testbench            )
  g.add_step( post_pnr_power       )
  g.add_step( custom_cts           )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------
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
  g.connect_by_name( adk,                  lvs            )
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
  g.connect_by_name( gen_sram,             genlibdb       )
  g.connect_by_name( gen_sram,             pt_signoff     )
  g.connect_by_name( gen_sram,             drc            )
  g.connect_by_name( gen_sram,             lvs            )
  g.connect_by_name( rtl,                  synth          )
  g.connect_by_name( constraints,          synth          )
  g.connect_by_name( custom_genus_scripts, synth          )
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
  g.connect_by_name( iflow,                postroute      )
  g.connect_by_name( iflow,                postroute_hold )
  g.connect_by_name( iflow,                signoff        )
  g.connect_by_name( custom_init,          init           )
  g.connect_by_name( custom_power,         power          )
  g.connect_by_name( custom_lvs,           lvs            )
  g.connect_by_name( init,                 power          )
  g.connect_by_name( power,                place          )
  g.connect_by_name( place,                cts            )
  g.connect_by_name( cts,                  postcts_hold   )
  g.connect_by_name( postcts_hold,         route          )
  g.connect_by_name( route,                postroute      )
  g.connect_by_name( postroute,            postroute_hold )
  g.connect_by_name( postroute_hold,       signoff        )
  g.connect_by_name( signoff,              drc            )
  g.connect_by_name( signoff,              lvs            )
  g.connect_by_name( signoff,              genlibdb       )
  g.connect_by_name( adk,                  genlibdb       )
  g.connect_by_name( genlibdb_constraints, genlibdb       )
  g.connect_by_name( genlibdb,             lib2db         )
  g.connect_by_name( adk,                  pt_signoff     )
  g.connect_by_name( signoff,              pt_signoff     )
  g.connect_by_name( application,          testbench      )
  g.connect_by_name( application,          post_pnr_power )
  g.connect_by_name( gen_sram,             post_pnr_power )
  g.connect_by_name( signoff,              post_pnr_power )
  g.connect_by_name( pt_signoff,           post_pnr_power )
  g.connect_by_name( testbench,            post_pnr_power )
  g.connect_by_name( adk,                  debugcalibre   )
  g.connect_by_name( synth,                debugcalibre   )
  g.connect_by_name( iflow,                debugcalibre   )
  g.connect_by_name( signoff,              debugcalibre   )
  g.connect_by_name( custom_cts,           cts            )
  g.connect_by_name( iflow,                genlibdb       )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  # Used in floorplan.tcl
  init.update_params(  { 'adk': parameters['adk'] }, True )

  # Core density target param
  init.update_params( { 'core_density_target': parameters['core_density_target'] }, True )

  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

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
    # 'add-tracks.tcl',
    # 'create-boundary-blockage.tcl',
    'place-dic-cells.tcl',
    'create-special-grid.tcl',
    'add-endcaps-welltaps.tcl',
    'insert-input-antenna-diodes.tcl',
    'make-path-groups.tcl',
    'additional-path-groups.tcl',
    # 'sram-hold-false-path.tcl', # somehow it has problem
    'reporting.tcl'
  ] } )

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

  # Adding new input for genlibdb node to run
  # gf12 uses synopsys-ptpx for genlib (default is cadence-genus)
  order = genlibdb.get_param('order') # get the default script run order
  extraction_idx = order.index( 'extract_model.tcl' ) # find extract_model.tcl
  order.insert( extraction_idx, 'genlibdb-constraints.tcl' ) # add here
  genlibdb.update_params( { 'order': order } )
  # genlibdb -- Remove 'report-interface-timing.tcl' beacuse it takes
  # very long and is not necessary
  order = genlibdb.get_param('order')
  order.remove( 'write-interface-timing.tcl' )
  genlibdb.update_params( { 'order': order } )
  return g

if __name__ == '__main__':
  g = construct()
#  g.plot()


