#! /usr/bin/env python
#=========================================================================
# construct.py
#=========================================================================
# Author : 
# Date   : 
#

import os
import sys

from mflowgen.components import Graph, Step, Subgraph
from shutil import which
from common.get_sys_adk import get_sys_adk

def construct():

  g = Graph()

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  adk_name = get_sys_adk()
  adk_view = 'multivt'
  which_soc = 'opal'

  parameters = {
    'construct_path'    : __file__,
    'design_name'       : 'MatrixUnit',
    'clock_period'      : 1.2 * 1000,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    'adk_stdcell'       : 'b0m_6t_108pp',
    'adk_libmodel'      : 'nldm',
    # Synthesis
    'flatten_effort'    : 3,
    'topographical'     : True,
    # RTL Generation
    'array_width'         : 28,
    'array_height'        : 16,
    'num_glb_tiles'       : 14,
    'glb_tile_mem_size'   : 128,
    'interconnect_only'   : False,
    'use_local_garnet'    : False,
    'PWR_AWARE'           : False,
    'soc_only'            : False,
    'include_core'        : 1,
    'rtl_docker_image'    : 'default', # Current default is 'stanfordaha/garnet:latest'
    # MatrixUnit P&R parameters
    'pe_array_width'      : 32,
    'pe_array_height'     : 64,
    # Useful Skew (CTS)
    'useful_skew'       : False,
    # hold target slack
    'hold_target_slack' : 0.07,
    'drc_env_setup'     : 'drcenv-block.sh'
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
  processing_element = Subgraph( this_dir + '/../ProcessingElement', 'ProcessingElement' )

  # Custom steps
  rtl            = Step( this_dir + '/../common/rtl'                          )
  constraints    = Step( this_dir + '/constraints'                            )
  custom_init    = Step( this_dir + '/custom-init'                            )
  custom_power   = Step( this_dir + '/../common/custom-power-hierarchical'    )
  custom_cts     = Step( this_dir + '/custom-cts-overrides'                   )
  gls_args       = Step( this_dir + '/gls_args'                               )
  custom_flowgen_setup = Step( this_dir + '/custom-flowgen-setup'             )
  custom_hack_sdc_unit = Step( this_dir + '/../common/custom-hack-sdc-unit'   )
  custom_hack_lef_ante = Step( this_dir + '/../common/custom-hack-lef-antenna')
  gen_sram_iw    = Step( this_dir + '/../common/gen_sram_macro'               )
  gen_sram_accum = Step( this_dir + '/../common/gen_sram_macro'               )

  # Default steps
  info           = Step( 'info',                           default=True )
  synth          = Step( 'cadence-genus-synthesis',        default=True )
  iflow          = Step( 'cadence-innovus-flowsetup',      default=True )
  init           = Step( 'cadence-innovus-init',           default=True )
  power          = Step( 'cadence-innovus-power',          default=True )
  place          = Step( 'cadence-innovus-place',          default=True )
  cts            = Step( 'cadence-innovus-cts',            default=True )
  postcts_hold   = Step( 'cadence-innovus-postcts_hold',   default=True )
  route          = Step( 'cadence-innovus-route',          default=True )
  postroute      = Step( 'cadence-innovus-postroute',      default=True )
  postroute_hold = Step( 'cadence-innovus-postroute_hold', default=True )
  signoff        = Step( 'cadence-innovus-signoff',        default=True )
  pt_signoff     = Step( 'synopsys-pt-timing-signoff',     default=True )
  genlibdb_tt    = Step( 'synopsys-ptpx-genlibdb',         default=True )
  genlibdb_ff    = Step( 'synopsys-ptpx-genlibdb',         default=True )
  debugcalibre   = Step( 'cadence-innovus-debug-calibre',  default=True )
  drc            = Step( this_dir + '/../common/intel16-synopsys-icv-drc' )
  lvs            = Step( this_dir + '/../common/intel16-synopsys-icv-lvs' )

  genlibdb_tt.set_name( 'synopsys-ptpx-genlibdb-tt' )
  genlibdb_ff.set_name( 'synopsys-ptpx-genlibdb-ff' )
  gen_sram_iw.set_name( 'gen_sram_iw' )
  gen_sram_accum.set_name( 'gen_sram_accum' )

  # ----- SRAM info
  # SRAM Families:
  # SRAM_1P: single-port SRAM
  # RF_2P: two-port register file
  gen_sram_iw.update_params( {
      'sram_family': "SRAM_1P",
      'num_words': 1024,
      'word_size': 64,
      'mux_size': 4,
      'tt_corner': "tttt_0.85v_25c",
      'bc_corner': "pfff_0.89v_-40c",
      'wc_corner': "psss_0.765v_125c",
      'partial_write': 0
  } )
  gen_sram_accum.update_params( {
      'sram_family': "RF_2P",
      'num_words': 1024,
      'word_size': 64,
      'mux_size': 2,
      'tt_corner': "tttt_0.85v_25c",
      'bc_corner': "pfff_0.89v_-40c",
      'wc_corner': "psss_0.765v_125c",
      'partial_write': 0
  } )

  # Add macro info to downstream nodes
  synth.extend_inputs( ['ProcessingElement-typical.lib', 'ProcessingElement.lef'] )
  iflow.extend_inputs( custom_flowgen_setup.all_outputs() )
  pt_signoff.extend_inputs( ['ProcessingElement-typical.db'] )
  pt_signoff.extend_inputs( ['ProcessingElement-bc.db'] )
  genlibdb_tt.extend_inputs( ['ProcessingElement-typical.db'] )
  genlibdb_ff.extend_inputs( ['ProcessingElement-bc.db'] )

  # Add extra input edges to innovus steps that need custom tweaks
  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )
  cts.extend_inputs( custom_cts.all_outputs() )

  # SDC hack for the genlibdb and pt_signoff steps
  genlibdb_tt.extend_inputs( custom_hack_sdc_unit.all_outputs() )
  genlibdb_ff.extend_inputs( custom_hack_sdc_unit.all_outputs() )
  pt_signoff.extend_inputs( custom_hack_sdc_unit.all_outputs() )

  # LEF antenna hack
  adk.extend_inputs( custom_hack_lef_ante.all_outputs() )
  
  # Inputs
  g.add_input( 'design.v', rtl.i('design.v') )
  g.add_input( 'header'  , rtl.i('header')   )

  # Outputs (MatrixUnit)
  g.add_output( 'MatrixUnit-typical.lib',            genlibdb_tt.o('design.lib')          )
  g.add_output( 'MatrixUnit-typical.db',             genlibdb_tt.o('design.db')           )
  g.add_output( 'MatrixUnit-bc.lib',                 genlibdb_ff.o('design.lib')          )
  g.add_output( 'MatrixUnit-bc.db',                  genlibdb_ff.o('design.db')           )
  g.add_output( 'MatrixUnit.lef',                    signoff.o('design.lef')              )
  g.add_output( 'MatrixUnit.vcs.v',                  signoff.o('design.vcs.v')            )
  g.add_output( 'MatrixUnit.sdf',                    signoff.o('design.sdf')              )
  g.add_output( 'MatrixUnit.oas',                    signoff.o('design-merged.oas')       )
  g.add_output( 'MatrixUnit.lvs.v',                  lvs.o('design_merged.lvs.v')         )
  g.add_output( 'MatrixUnit.vcs.pg.v',               signoff.o('design.vcs.pg.v')         )
  g.add_output( 'MatrixUnit.spef.gz',                signoff.o('design.spef.gz')          )
  # Outputs (MatrixUnit_sram_iw)
  g.add_output( 'MatrixUnit_sram_iw.spi',            gen_sram_iw.o('sram.spi')            )
  g.add_output( 'MatrixUnit_sram_iw.v',              gen_sram_iw.o('sram.v')              )
  g.add_output( 'MatrixUnit_sram_iw-bc.db',          gen_sram_iw.o('sram-bc.db')          )
  g.add_output( 'MatrixUnit_sram_iw-bc.lib',         gen_sram_iw.o('sram-bc.lib')         )
  g.add_output( 'MatrixUnit_sram_iw-wc.db',          gen_sram_iw.o('sram-wc.db')          )
  g.add_output( 'MatrixUnit_sram_iw-wc.lib',         gen_sram_iw.o('sram-wc.lib')         )
  g.add_output( 'MatrixUnit_sram_iw-typical.db',     gen_sram_iw.o('sram-typical.db')     )
  g.add_output( 'MatrixUnit_sram_iw-typical.lib',    gen_sram_iw.o('sram-typical.lib')    )
  # Outputs (MatrixUnit_sram_accum)
  g.add_output( 'MatrixUnit_sram_accum.spi',         gen_sram_accum.o('sram.spi')         )
  g.add_output( 'MatrixUnit_sram_accum.v',           gen_sram_accum.o('sram.v')           )
  g.add_output( 'MatrixUnit_sram_accum-bc.db',       gen_sram_accum.o('sram-bc.db')       )
  g.add_output( 'MatrixUnit_sram_accum-bc.lib',      gen_sram_accum.o('sram-bc.lib')      )
  g.add_output( 'MatrixUnit_sram_accum-wc.db',       gen_sram_accum.o('sram-wc.db')       )
  g.add_output( 'MatrixUnit_sram_accum-wc.lib',      gen_sram_accum.o('sram-wc.lib')      )
  g.add_output( 'MatrixUnit_sram_accum-typical.db',  gen_sram_accum.o('sram-typical.db')  )
  g.add_output( 'MatrixUnit_sram_accum-typical.lib', gen_sram_accum.o('sram-typical.lib') )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info           )
  g.add_step( rtl            )
  g.add_step( processing_element)
  g.add_step( constraints    )
  g.add_step( synth          )
  g.add_step( custom_flowgen_setup )
  g.add_step( iflow          )
  g.add_step( init           )
  g.add_step( custom_init    )
  g.add_step( power          )
  g.add_step( custom_power   )
  g.add_step( place          )
  g.add_step( custom_cts     )
  g.add_step( cts            )
  g.add_step( postcts_hold   )
  g.add_step( route          )
  g.add_step( postroute      )
  g.add_step( postroute_hold )
  g.add_step( signoff        )
  g.add_step( pt_signoff     )
  g.add_step( drc            )
  g.add_step( lvs            )
  g.add_step( debugcalibre   )
  g.add_step( gls_args       )
  g.add_step( genlibdb_tt    )
  g.add_step( genlibdb_ff    )
  g.add_step( custom_hack_sdc_unit )
  g.add_step( custom_hack_lef_ante )
  g.add_step( gen_sram_iw    )
  g.add_step( gen_sram_accum )

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
  g.connect_by_name( adk,      gen_sram_iw    )
  g.connect_by_name( adk,      gen_sram_accum )

  #-----------------------------------------------------------------------
  # Graph -- Add edges for SRAMs
  #-----------------------------------------------------------------------
  # These PD steps need lib/lef files for the SRAMs
  for step in [synth, iflow, init, power, place, cts, postcts_hold, route, postroute, postroute_hold, signoff]:
    step.extend_inputs( ['sram_iw-typical.lib', 'sram_iw-bc.lib', 'sram_iw.lef'] )
    step.extend_inputs( ['sram_accum-typical.lib', 'sram_accum-bc.lib', 'sram_accum.lef'] )
  # PTPX Signoff / genlibdb needs .db files
  pt_signoff.extend_inputs( ['sram_iw-typical.db', 'sram_iw-bc.db', 'sram_accum-typical.db', 'sram_accum-bc.db'] )
  genlibdb_tt.extend_inputs( ['sram_iw-typical.db', 'sram_accum-typical.db'] )
  genlibdb_ff.extend_inputs( ['sram_iw-bc.db', 'sram_accum-bc.db'] )
  # Signoff needs the merged OASIS file
  signoff.extend_inputs( ['sram_iw.oas'] )
  signoff.extend_inputs( ['sram_accum.oas'] )
  # LVS node need spi
  lvs.extend_inputs( ['sram_iw.spi'] )
  lvs.extend_inputs( ['sram_accum.spi'] )
  # Connect gen_sram_macro node(s) to all downstream nodes that need them
  nodes_need_sram = [synth, iflow, init, power, place, cts, postcts_hold,
                route, postroute, postroute_hold, signoff, pt_signoff,
                genlibdb_tt, genlibdb_ff, lvs]
  for node in nodes_need_sram:
    for sram_output in gen_sram_iw.all_outputs():
      node_input = sram_output.replace('sram', 'sram_iw')
      if node_input in node.all_inputs():
        g.connect(gen_sram_iw.o(sram_output), node.i(node_input))
    for sram_output in gen_sram_accum.all_outputs():
      node_input = sram_output.replace('sram', 'sram_accum')
      if node_input in node.all_inputs():
        g.connect(gen_sram_accum.o(sram_output), node.i(node_input))

  # inputs to ProcessingElement
  g.connect_by_name( rtl, processing_element )
  # outputs from ProcessingElement
  g.connect_by_name( processing_element,      synth          )
  g.connect_by_name( processing_element,      iflow          )
  g.connect_by_name( processing_element,      init           )
  g.connect_by_name( processing_element,      power          )
  g.connect_by_name( processing_element,      place          )
  g.connect_by_name( processing_element,      cts            )
  g.connect_by_name( processing_element,      postcts_hold   )
  g.connect_by_name( processing_element,      route          )
  g.connect_by_name( processing_element,      postroute      )
  g.connect_by_name( processing_element,      postroute_hold )
  g.connect_by_name( processing_element,      signoff        )
  g.connect_by_name( processing_element,      pt_signoff     )
  g.connect_by_name( processing_element,      drc            )
  g.connect_by_name( processing_element,      lvs            )
  g.connect_by_name( processing_element,      genlibdb_tt    )
  g.connect_by_name( processing_element,      genlibdb_ff    )

  g.connect_by_name( rtl,            synth        )
  g.connect_by_name( rtl,            synth        )
  g.connect_by_name( constraints,    synth        )

  g.connect_by_name( synth,       iflow        )
  g.connect_by_name( synth,       init         )
  g.connect_by_name( synth,       power        )
  g.connect_by_name( synth,       place        )
  g.connect_by_name( synth,       cts          )
  
  g.connect_by_name( custom_flowgen_setup,  iflow )
  g.connect_by_name( iflow,    init           )
  g.connect_by_name( iflow,    power          )
  g.connect_by_name( iflow,    place          )
  g.connect_by_name( iflow,    cts            )
  g.connect_by_name( iflow,    postcts_hold   )
  g.connect_by_name( iflow,    route          )
  g.connect_by_name( iflow,    postroute      )
  g.connect_by_name( iflow,    postroute_hold )
  g.connect_by_name( iflow,    signoff        )

  g.connect_by_name( custom_init,  init     )
  g.connect_by_name( custom_power, power    )
  g.connect_by_name( custom_cts, cts        )

  g.connect_by_name( init,         power          )
  g.connect_by_name( power,        place          )
  g.connect_by_name( place,        cts            )
  g.connect_by_name( cts,          postcts_hold   )
  g.connect_by_name( postcts_hold, route          )
  g.connect_by_name( route,        postroute      )
  g.connect_by_name( postroute,    postroute_hold )
  g.connect_by_name( postroute_hold, signoff      )
  g.connect_by_name( signoff,      drc            )
  g.connect_by_name( signoff,      lvs            )

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )

  g.connect_by_name( adk,          genlibdb_tt )
  g.connect_by_name( adk,          genlibdb_ff )
  g.connect_by_name( signoff,      genlibdb_tt )
  g.connect_by_name( signoff,      genlibdb_ff )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( synth,    debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( drc,      debugcalibre )
  g.connect_by_name( lvs,      debugcalibre )

  # SDC hack for the genlibdb and pt_signoff steps
  g.connect_by_name( custom_hack_sdc_unit, genlibdb_tt )
  g.connect_by_name( custom_hack_sdc_unit, genlibdb_ff )
  g.connect_by_name( custom_hack_sdc_unit, pt_signoff )

  # LEF antenna hack
  g.connect_by_name( custom_hack_lef_ante, adk )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  # genlibdb parameters
  genlibdb_tt.update_params({
    'corner': 'typical'
  })
  genlibdb_ff.update_params({
    'corner': 'bc'
  })

  # Add SDC unit hack before genlibdb and pt_signoff
  sdc_hack_command = "python inputs/hack_sdc_unit.py inputs/design.pt.sdc"

  # The SDC file generated by Innovus contains -library flag to explicitly
  # specify which library to use for the cell. However, we will change the
  # target library for different corners and that makes the SDC commands
  # fail to find the cell. We should remove the -library flag and let the
  # tool find the cell from the target library (default behavior).
  sdc_filter_command = "sed -i 's/-library [^ ]* //g' inputs/design.pt.sdc"

  # add the commands to the steps
  genlibdb_tt.pre_extend_commands( [sdc_hack_command, sdc_filter_command] )
  genlibdb_ff.pre_extend_commands( [sdc_hack_command, sdc_filter_command] )
  pt_signoff.pre_extend_commands( [sdc_hack_command, sdc_filter_command] )

  # init -- update custom order
  init.update_params( { 'order': init_order } )

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

  synth_postconditions = synth.get_postconditions()
  for postcon in synth_postconditions:
      if 'percent_clock_gated' in postcon:
          synth_postconditions.remove(postcon)
  synth.set_postconditions( synth_postconditions )

  return g

if __name__ == '__main__':
  g = construct()
#  g.plot()


