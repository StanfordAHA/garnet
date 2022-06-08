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

def sr_override_parms(parmdict):
  '''
  # A mechanism whereby e.g. buildkite can alter parms at the last minute
  # by way of environmental variables e.g. for faster postroute_hold step
  # could do something like
  #    export MFLOWGEN_PARM_OVERRIDE_hold_target_slack=0.6
  #    mflowgen run --design $$GARNET_HOME/mflowgen/full_chip
  #    make cadence-innovus-postroute_hold
'''
  import os
  for e in os.environ:
    # e.g. e="MFLOWGEN_PARM_OVERRIDE_hold_target_slack"
    if e[0:22]=="MFLOWGEN_PARM_OVERRIDE":
      parm=e[23:99];     # e.g. parm="hold_target_slack"
      print(f'+++ FOUND MFLOWGEN PARAMETER OVERRIDE "{parm}={os.environ[e]}"')
      print(f'BEFOR: parmdict["hold_target_slack"]={parmdict["hold_target_slack"]}')
      parmdict[parm]=os.environ[e]
  print(f'AFTER: parmdict["hold_target_slack"]={parmdict["hold_target_slack"]}')


  return(parmdict)


def construct():

  g = Graph()

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  adk_name = get_sys_adk()
  adk_view = 'view-standard'

  if which("calibre") is not None:
      drc_rule_deck = 'calibre-drc-chip.rule'
      antenna_drc_rule_deck = 'calibre-drc-antenna.rule'
      power_drc_rule_deck = 'calibre-drc-block.rule'
  else:
      drc_rule_deck = 'pegasus-drc-chip.rule'
      antenna_drc_rule_deck = 'pegasus-drc-antenna.rule'
      power_drc_rule_deck = 'pegasus-drc-block.rule'

  parameters = {
    'construct_path'    : __file__,
    'design_name'       : 'GarnetSOC_pad_frame',
    'clock_period'      : 1.3,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    # Synthesis
    'flatten_effort'    : 0,
    'topographical'     : True,
    # RTL Generation
    'array_width'       : 32,
    'array_height'      : 16,
    'num_glb_tiles'     : 16,
    'interconnect_only' : False,
    # glb tile memory size (unit: KB)
    # 'glb_tile_mem_size' : 64,  #  64x16 => 1M global buffer
    'glb_tile_mem_size' : 256,   # 256*16 => 4M global buffer
    # Power Domains
    'PWR_AWARE'         : True,
    # Include Garnet?
    'soc_only'          : False,
    # Include SoC core? (use 0 for false, 1 for true)
    'include_core'      : 1,
    # Include sealring?
    'include_sealring'  : True,
    # SRAM macros
    'num_words'         : 2048,
    'word_size'         : 64,
    'mux_size'          : 8,
    'corner'            : "tt0p8v25c",
    'partial_write'     : True,
    # Dragonphy
    'dragonphy_rdl_x'   : '613.565u',
    'dragonphy_rdl_y'   : '3901.872u',
    # Low Effort flow
    'express_flow'             : False,
    'skip_verify_connectivity' : True,
    # Hold fixing
    'signoff_engine' : True,
    'hold_target_slack'  : 0.060,
    # LVS
    # - need lvs2 because dragonphy uses LVT cells
    'lvs_extra_spice_include' : 'inputs/adk_lvs2/*.cdl',
    'lvs_hcells_file'   : 'inputs/adk/hcells.inc',
    'lvs_connect_names' : '"VDD VSS VDDPST"',
    'lvs_verify_netlist' : 0,
    # TSMC16 support for LVS - need lvs2 because dragonphy uses LVT cells
    'adk_view_lvs2'     : 'multivt',
    # TLX Ports Partitions
    'TLX_FWD_DATA_LO_WIDTH' : 16,
    'TLX_REV_DATA_LO_WIDTH' : 45,
    # DRC rule deck
    'drc_rule_deck'         : drc_rule_deck,
    'antenna_drc_rule_deck' : antenna_drc_rule_deck,
    'power_drc_rule_deck'   : power_drc_rule_deck,
    'nthreads'              : 16,
    # Testbench
    'cgra_apps' : ["tests/conv_1_2", "tests/conv_2_1"]
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl            = Step( this_dir + '/../common/rtl'                       )
  soc_rtl        = Step( this_dir + '/../common/soc-rtl-v2'                )
  gen_sram       = Step( this_dir + '/../common/gen_sram_macro'            )
  constraints    = Step( this_dir + '/constraints'                         )
  read_design    = Step( this_dir + '/../common/fc-custom-read-design'     )
  custom_init    = Step( this_dir + '/custom-init'                         )
  custom_lvs     = Step( this_dir + '/custom-lvs-rules'                    )
  custom_power   = Step( this_dir + '/../common/custom-power-chip'         )
  init_fc        = Step( this_dir + '/../common/init-fullchip'             )
  io_file        = Step( this_dir + '/io_file'                             )
  pre_route      = Step( this_dir + '/pre-route'                           )
  sealring       = Step( this_dir + '/sealring'                            )
  netlist_fixing = Step( this_dir + '/../common/fc-netlist-fixing'         )

  # Block-level designs

  tile_array        = Step( this_dir + '/tile_array'        )
  glb_top           = Step( this_dir + '/glb_top'           )
  global_controller = Step( this_dir + '/global_controller' )
  dragonphy         = Step( this_dir + '/dragonphy'         )

  # CGRA simulation

  cgra_rtl_sim_compile  = Step( this_dir + '/cgra_rtl_sim_compile' )
  cgra_rtl_sim_run      = Step( this_dir + '/cgra_rtl_sim_run'     )
  cgra_sim_build        = Step( this_dir + '/cgra_sim_build'       )
  # cgra_gl_sim_compile   = Step( this_dir + '/cgra_gl_sim_compile'  )
  # cgra_gl_sim_run       = Step( this_dir + '/cgra_gl_sim_run'      )
  # cgra_gl_ptpx          = Step( this_dir + '/cgra_gl_ptpx'         )
  # cgra_rtl_sim_verdict  = Step( this_dir + '/cgra_rtl_sim_verdict' )
  # cgra_gl_sim_verdict   = Step( this_dir + '/cgra_gl_sim_verdict'  )

  # Default steps

  info           = Step( 'info',                          default=True )
  #constraints    = Step( 'constraints',                   default=True )
  synth          = Step( 'cadence-genus-synthesis',       default=True )
  iflow          = Step( 'cadence-innovus-flowsetup',     default=True )
  init           = Step( 'cadence-innovus-init',          default=True )
  power          = Step( 'cadence-innovus-power',         default=True )
  place          = Step( 'cadence-innovus-place',         default=True )
  cts            = Step( 'cadence-innovus-cts',           default=True )
  postcts_hold   = Step( 'cadence-innovus-postcts_hold',  default=True )
  route          = Step( 'cadence-innovus-route',         default=True )
  postroute      = Step( 'cadence-innovus-postroute',     default=True )
  postroute_hold = Step( 'cadence-innovus-postroute_hold', default=True )
  signoff        = Step( 'cadence-innovus-signoff',       default=True )
  pt_signoff     = Step( 'synopsys-pt-timing-signoff',    default=True )
  if which("calibre") is not None:
      drc            = Step( 'mentor-calibre-drc',            default=True )
      lvs            = Step( 'mentor-calibre-lvs',            default=True )
      merge_rdl      = Step( 'mentor-calibre-gdsmerge-child', default=True )
      fill           = Step( 'mentor-calibre-fill',           default=True )
      merge_fill     = Step( 'mentor-calibre-gdsmerge-child', default=True )
  else:
      drc            = Step( 'cadence-pegasus-drc',            default=True )
      lvs            = Step( 'cadence-pegasus-lvs',            default=True )
      merge_rdl      = Step( 'cadence-pegasus-gdsmerge-child', default=True )
      fill           = Step( 'cadence-pegasus-fill',           default=True )
      merge_fill     = Step( 'cadence-pegasus-gdsmerge-child', default=True )
  debugcalibre   = Step( 'cadence-innovus-debug-calibre', default=True )

  merge_rdl.set_name('gdsmerge-dragonphy-rdl')
  merge_fill.set_name('gdsmerge-fill')

  # Send in the clones
  # 'power' step now gets its own design-rule check
  power_drc = drc.clone()
  power_drc.set_name( 'power-drc' )

  # Antenna DRC Check
  antenna_drc = drc.clone()
  antenna_drc.set_name( 'antenna-drc' )

  # Add cgra tile macro inputs to downstream nodes

  synth.extend_inputs( ['tile_array_tt.lib', 'tile_array.lef'] )
  synth.extend_inputs( ['glb_top_tt.lib', 'glb_top.lef'] )
  synth.extend_inputs( ['global_controller_tt.lib', 'global_controller.lef'] )
  synth.extend_inputs( ['sram_tt.lib', 'sram.lef'] )
  synth.extend_inputs( ['dragonphy_top.lef'] )
  # Exclude dragonphy_top from synth inputs to prevent floating
  # dragonphy inputs from being tied to 0
  pt_signoff.extend_inputs( ['tile_array_tt.db'] )
  pt_signoff.extend_inputs( ['glb_top_tt.db'] )
  pt_signoff.extend_inputs( ['global_controller_tt.db'] )
  pt_signoff.extend_inputs( ['sram_tt.db'] )
  pt_signoff.extend_inputs( ['dragonphy_top_tt.db'] )

  route.extend_inputs( ['pre-route.tcl'] )
  signoff.extend_inputs( sealring.all_outputs() )
  signoff.extend_inputs( netlist_fixing.all_outputs() )
  # These steps need timing info for cgra tiles

  hier_steps = \
    [ iflow, init, power, place, cts, postcts_hold,
      route, postroute, signoff]

  for step in hier_steps:
    step.extend_inputs( ['tile_array_tt.lib', 'tile_array.lef'] )
    step.extend_inputs( ['glb_top_tt.lib', 'glb_top.lef'] )
    step.extend_inputs( ['global_controller_tt.lib', 'global_controller.lef'] )
    step.extend_inputs( ['sram_tt.lib', 'sram.lef'] )
    step.extend_inputs( ['dragonphy_top_tt.lib', 'dragonphy_top.lef'] )
    step.extend_inputs( ['dragonphy_RDL.lef'] )

  # Need all block gds's to merge into the final layout
  gdsmerge_nodes = [signoff, power]
  for node in gdsmerge_nodes:
      node.extend_inputs( ['tile_array.gds'] )
      node.extend_inputs( ['glb_top.gds'] )
      node.extend_inputs( ['global_controller.gds'] )
      node.extend_inputs( ['sram.gds'] )
      node.extend_inputs( ['dragonphy_top.gds'] )
      node.extend_inputs( ['dragonphy_RDL.gds'] )

  # Need extracted spice files for both tile types to do LVS

  lvs.extend_inputs( ['tile_array.lvs.v'] )
  lvs.extend_inputs( ['tile_array.sram.spi'] )
  lvs.extend_inputs( ['glb_top.lvs.v'] )
  lvs.extend_inputs( ['glb_top.sram.spi'] )
  lvs.extend_inputs( ['global_controller.lvs.v'] )
  lvs.extend_inputs( ['sram.spi'] )
  lvs.extend_inputs( ['dragonphy_top.spi'] )
  lvs.extend_inputs( ['adk_lvs2'] )

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  init.extend_inputs( init_fc.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  synth.extend_inputs( soc_rtl.all_outputs() )
  synth.extend_inputs( read_design.all_outputs() )
  synth.extend_inputs( ["cons_scripts"] )

  power.extend_outputs( ["design-merged.gds"] )

  if parameters['interconnect_only'] is False:
    rtl.extend_outputs( ['header'] )
    rtl.extend_postconditions( ["assert File( 'outputs/header' ) "] )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info              )
  g.add_step( rtl               )
  g.add_step( soc_rtl           )
  g.add_step( gen_sram          )
  g.add_step( tile_array        )
  g.add_step( glb_top           )
  g.add_step( global_controller )
  g.add_step( dragonphy         )
  g.add_step( constraints       )
  g.add_step( read_design       )
  g.add_step( synth             )
  g.add_step( iflow             )
  g.add_step( init              )
  g.add_step( init_fc           )
  g.add_step( io_file           )
  g.add_step( custom_init       )
  g.add_step( power             )
  g.add_step( custom_power      )
  g.add_step( place             )
  g.add_step( cts               )
  g.add_step( postcts_hold      )
  g.add_step( pre_route         )
  g.add_step( route             )
  g.add_step( postroute         )
  g.add_step( postroute_hold    )
  g.add_step( sealring          )
  g.add_step( netlist_fixing    )
  g.add_step( signoff           )
  g.add_step( pt_signoff        )
  g.add_step( merge_rdl         )
  g.add_step( fill              )
  g.add_step( merge_fill        )
  g.add_step( drc               )
  g.add_step( antenna_drc       )
  g.add_step( lvs               )
  g.add_step( custom_lvs        )
  g.add_step( debugcalibre      )

  # Post-Power DRC check
  g.add_step( power_drc         )

  # App test nodes
  g.add_step( cgra_rtl_sim_compile )
  g.add_step( cgra_sim_build       )
  g.add_step( cgra_rtl_sim_run     )
  # g.add_step( cgra_gl_sim_compile )

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
  g.connect_by_name( adk,      merge_rdl      )
  g.connect_by_name( adk,      fill           )
  g.connect_by_name( adk,      merge_fill     )
  g.connect_by_name( adk,      drc            )
  g.connect_by_name( adk,      antenna_drc    )
  g.connect_by_name( adk,      lvs            )

  # Post-Power DRC check
  g.connect_by_name( adk,      power_drc )

  # Connect RTL verification nodes
  g.connect_by_name( rtl, cgra_rtl_sim_compile )
  g.connect_by_name( cgra_sim_build, cgra_rtl_sim_run )
  g.connect_by_name( cgra_rtl_sim_compile, cgra_rtl_sim_run )

  # Connect GL verification nodes
  # g.connect_by_name( signoff, cgra_gl_sim_compile )

  # All of the blocks within this hierarchical design
  # Skip these if we're doing soc_only
  if parameters['soc_only'] == False:
      blocks = [tile_array, glb_top, global_controller, dragonphy]
      for block in blocks:
          g.connect_by_name( block, synth          )
          g.connect_by_name( block, iflow          )
          g.connect_by_name( block, init           )
          g.connect_by_name( block, power          )
          g.connect_by_name( block, place          )
          g.connect_by_name( block, cts            )
          g.connect_by_name( block, postcts_hold   )
          g.connect_by_name( block, route          )
          g.connect_by_name( block, postroute      )
          g.connect_by_name( block, postroute_hold )
          g.connect_by_name( block, signoff        )
          g.connect_by_name( block, pt_signoff     )
          g.connect_by_name( block, drc            )
          g.connect_by_name( block, lvs            )
      # Tile_array can use rtl from rtl node
      g.connect_by_name( rtl, tile_array )
      # glb_top can use rtl from rtl node
      g.connect_by_name( rtl, glb_top )
      # global_controller can use rtl from rtl node
      g.connect_by_name( rtl, global_controller )

  g.connect_by_name( rtl,         synth     )
  g.connect_by_name( soc_rtl,     synth        )
  g.connect_by_name( constraints, synth        )
  g.connect_by_name( read_design, synth        )

  g.connect_by_name( soc_rtl,  io_file      )

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
  g.connect_by_name( iflow,    postroute      )
  g.connect_by_name( iflow,    postroute_hold )
  g.connect_by_name( iflow,    signoff        )

  g.connect_by_name( custom_init,  init     )
  g.connect_by_name( custom_lvs,   lvs      )
  g.connect_by_name( custom_power, power    )

  # SRAM macro
  g.connect_by_name( gen_sram, synth          )
  g.connect_by_name( gen_sram, iflow          )
  g.connect_by_name( gen_sram, init           )
  g.connect_by_name( gen_sram, power          )
  g.connect_by_name( gen_sram, place          )
  g.connect_by_name( gen_sram, cts            )
  g.connect_by_name( gen_sram, postcts_hold   )
  g.connect_by_name( gen_sram, route          )
  g.connect_by_name( gen_sram, postroute      )
  g.connect_by_name( gen_sram, postroute_hold )
  g.connect_by_name( gen_sram, signoff        )
  g.connect_by_name( gen_sram, pt_signoff     )
  g.connect_by_name( gen_sram, drc            )
  g.connect_by_name( gen_sram, lvs            )

  # Full chip floorplan stuff
  g.connect_by_name( io_file, init_fc )
  g.connect_by_name( init_fc, init    )

  g.connect_by_name( init,           power          )
  g.connect_by_name( power,          place          )
  g.connect_by_name( place,          cts            )
  g.connect_by_name( cts,            postcts_hold   )
  g.connect_by_name( postcts_hold,   route          )
  g.connect_by_name( route,          postroute      )
  g.connect_by_name( postroute,      postroute_hold )
  g.connect_by_name( postroute_hold, signoff        )
  g.connect_by_name( signoff,        lvs            )
  g.connect(signoff.o('design-merged.gds'), drc.i('design_merged.gds'))
  g.connect(signoff.o('design-merged.gds'), lvs.i('design_merged.gds'))

  # Skipping
  g.connect( signoff.o('design-merged.gds'), merge_rdl.i('design.gds') )
  g.connect( dragonphy.o('dragonphy_RDL.gds'), merge_rdl.i('child.gds') )
  g.connect_by_name( merge_rdl, lvs )

  # Run Fill on merged GDS
  g.connect( merge_rdl.o('design_merged.gds'), fill.i('design.gds') )

  # Merge fill
  g.connect( merge_rdl.o('design_merged.gds'), merge_fill.i('design.gds') )
  g.connect( fill.o('fill.gds'), merge_fill.i('child.gds') )

  # Run DRC on merged and filled gds
  g.connect_by_name( merge_fill, drc )
  g.connect_by_name( merge_fill, antenna_drc )

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( synth,    debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( drc,      debugcalibre )
  g.connect_by_name( lvs,      debugcalibre )

  g.connect_by_name( pre_route, route )
  g.connect_by_name( sealring, signoff )
  g.connect_by_name( netlist_fixing, signoff )

  # Post-Power DRC
  g.connect(power.o('design-merged.gds'), power_drc.i('design_merged.gds'))
  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  # Allow user to override parms with env in a limited sort of way
  parameters = sr_override_parms( parameters )
  print(f'parameters["hold_target_slack"]={parameters["hold_target_slack"]}')
  g.update_params( parameters )

  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

  # DC needs these param to set the NO_CGRA macro
  synth.update_params({'soc_only': parameters['soc_only']}, True)
  # DC needs these params to set macros in soc rtl
  synth.update_params({'TLX_FWD_DATA_LO_WIDTH' : parameters['TLX_FWD_DATA_LO_WIDTH']}, True)
  synth.update_params({'TLX_REV_DATA_LO_WIDTH' : parameters['TLX_REV_DATA_LO_WIDTH']}, True)
  init.update_params({'soc_only': parameters['soc_only']}, True)

  init.update_params(
    {'order': [
      'main.tcl','quality-of-life.tcl',
      'stylus-compatibility-procs.tcl','floorplan.tcl','io-fillers.tcl',
      'alignment-cells.tcl',
      'analog-bumps/route-phy-bumps.tcl',
      'analog-bumps/bump-connect.tcl',
      'gen-bumps.tcl', 'check-bumps.tcl', 'route-bumps.tcl',
      'place-macros.tcl', 'dont-touch.tcl'
    ]}
  )

  # glb_top parameters update
  glb_top.update_params({'array_width': parameters['array_width']}, True)
  glb_top.update_params({'glb_tile_mem_size': parameters['glb_tile_mem_size']}, True)
  glb_top.update_params({'num_glb_tiles': parameters['num_glb_tiles']}, True)

  # App test parameters update
  cgra_rtl_sim_compile.update_params({'array_width': parameters['array_width']}, True)
  cgra_rtl_sim_compile.update_params({'array_height': parameters['array_height']}, True)
  cgra_rtl_sim_compile.update_params({'clock_period': parameters['clock_period']}, True)
  cgra_rtl_sim_compile.update_params({'glb_tile_mem_size': parameters['glb_tile_mem_size']}, True)

  cgra_rtl_sim_run.update_params({'cgra_apps': parameters['cgra_apps']}, True)

  # Power node order manipulation
  order = power.get_param('order')
  # Move endcap/welltap insertion to end of power step to improve runtime
  order.append( 'add-endcaps-welltaps.tcl' )
  # Stream out post-power GDS so that we can run DRC here
  order.append( 'innovus-foundation-flow/custom-scripts/stream-out.tcl' )
  order.append( 'attach-results-to-outputs.tcl' )
  power.update_params( { 'order': order } )

  # Add pre-route plugin to insert skip_routing commands
  order = route.get_param('order')
  order.insert( 0, 'pre-route.tcl' )
  route.update_params( { 'order': order } )

  # Signoff order additions
  order = signoff.get_param('order')
  # Add sealring at beginning of signoff, so it's in before we stream out GDS
  if parameters['include_sealring'] == True:
      order.insert(0, 'add-sealring.tcl')
  # Add netlist-fixing script before we save new netlist
  index = order.index( 'generate-results.tcl' )
  order.insert( index, 'netlist-fixing.tcl' )
  signoff.update_params( { 'order': order } )

  merge_rdl.update_params( {'coord_x': parameters['dragonphy_rdl_x'], 'coord_y': parameters['dragonphy_rdl_y'], 'flatten_child': True,
                            'design_top_cell': parameters['design_name'], 'child_top_cell': 'dragonphy_RDL'} )

  merge_fill.update_params( {'design_top_cell': parameters['design_name'], 'child_top_cell': f"{parameters['design_name']}_F16a"} )

  # Antenna DRC node needs to use antenna rule deck
  antenna_drc.update_params( { 'drc_rule_deck': parameters['antenna_drc_rule_deck'] } )

  # Power DRC node should use block level rule deck to improve runtimes and not report false errors
  power_drc.update_params( {'drc_rule_deck': parameters['power_drc_rule_deck'] } )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()
