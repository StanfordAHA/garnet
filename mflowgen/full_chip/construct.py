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
    'clock_period'      : 1.3,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    # Synthesis
    'flatten_effort'    : 1,
    'topographical'     : True,
    # RTL Generation
    'array_width'       : 32,
    'array_height'      : 16,
    'interconnect_only' : False,
    # Power Domains
    'PWR_AWARE'         : True,
    # Include Garnet?
    'soc_only'          : False,
    # Include SoC core? (use 0 for false, 1 for true)
    'include_core'      : 1,
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
    'lvs_hcells_file'   : 'inputs/adk/hcells.inc',
    'lvs_connect_names' : '"VDD VSS VDDPST"',
    'lvs_verify_netlist' : 0,
    # TLX Ports Partitions
    'TLX_FWD_DATA_LO_WIDTH' : 16,
    'TLX_REV_DATA_LO_WIDTH' : 45,
    # DRC rule deck
    'drc_rule_deck'         : 'calibre-drc-chip.rule',
    'antenna_drc_rule_deck' : 'calibre-drc-antenna.rule',
    'nthreads'              : 16
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

  # Default steps

  info           = Step( 'info',                          default=True )
  #constraints    = Step( 'constraints',                   default=True )
  dc             = Step( 'synopsys-dc-synthesis',         default=True )
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
  gdsmerge       = Step( 'mentor-calibre-gdsmerge',       default=True )
  merge_rdl      = Step( 'mentor-calibre-gdsmerge-child', default=True )
  drc            = Step( 'mentor-calibre-drc',            default=True )
  lvs            = Step( 'mentor-calibre-lvs',            default=True )
  debugcalibre   = Step( 'cadence-innovus-debug-calibre', default=True )
  fill           = Step( 'mentor-calibre-fill',           default=True )
  merge_fill     = Step( 'mentor-calibre-gdsmerge-child', default=True )

  merge_rdl.set_name('gdsmerge-dragonphy-rdl')
  merge_fill.set_name('gdsmerge-fill')

  # Send in the clones
  # 'power' step now gets its own design-rule check
  power_drc = drc.clone()
  power_drc.set_name( 'power-drc' )
  # "power" now builds a gds file for its own drc check "power_drc";
  # so need a gdsmerge step between the two
  power_gdsmerge = gdsmerge.clone()
  power_gdsmerge.set_name( 'power-gdsmerge' )

  # Antenna DRC Check
  antenna_drc = drc.clone()
  antenna_drc.set_name( 'antenna-drc' )


  # Add cgra tile macro inputs to downstream nodes

  dc.extend_inputs( ['tile_array.db'] )
  dc.extend_inputs( ['glb_top.db'] )
  dc.extend_inputs( ['global_controller.db'] )
  dc.extend_inputs( ['sram_tt.db'] )
  # Remove dragonphy_top from dc inputs to prevent floating
  # dragonphy inputs from being tied to 0
  # dc.extend_inputs( ['dragonphy_top_tt.db'] )
  pt_signoff.extend_inputs( ['tile_array.db'] )
  pt_signoff.extend_inputs( ['glb_top.db'] )
  pt_signoff.extend_inputs( ['global_controller.db'] )
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

  # Need the cgra tile gds's to merge into the final layout
  gdsmerge_nodes = [gdsmerge, power_gdsmerge]
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

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  init.extend_inputs( init_fc.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  dc.extend_inputs( soc_rtl.all_outputs() )
  dc.extend_inputs( read_design.all_outputs() )
  dc.extend_inputs( ["cons_scripts"] )

  power.extend_outputs( ["design.gds.gz"] )

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
  g.add_step( dc                )
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
  g.add_step( gdsmerge          )
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
  g.add_step( power_gdsmerge    )

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
  g.connect_by_name( adk,      merge_rdl      )
  g.connect_by_name( adk,      fill           )
  g.connect_by_name( adk,      merge_fill     )
  g.connect_by_name( adk,      drc            )
  g.connect_by_name( adk,      antenna_drc    )
  g.connect_by_name( adk,      lvs            )

  # Post-Power DRC check
  g.connect_by_name( adk,      power_gdsmerge )
  g.connect_by_name( adk,      power_drc )

  # All of the blocks within this hierarchical design
  # Skip these if we're doing soc_only
  if parameters['soc_only'] == False:
      blocks = [tile_array, glb_top, global_controller, dragonphy]
      for block in blocks:
          g.connect_by_name( block, dc             )
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
          g.connect_by_name( block, gdsmerge       )
          g.connect_by_name( block, power_gdsmerge )
          g.connect_by_name( block, drc            )
          g.connect_by_name( block, lvs            )
      # Tile_array can use rtl from rtl node
      g.connect_by_name( rtl, tile_array )

  g.connect_by_name( rtl,         dc        )
  g.connect_by_name( soc_rtl,     dc        )
  g.connect_by_name( constraints, dc        )
  g.connect_by_name( read_design, dc        )

  g.connect_by_name( soc_rtl,  io_file      )

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
  g.connect_by_name( iflow,    postroute      )
  g.connect_by_name( iflow,    postroute_hold )
  g.connect_by_name( iflow,    signoff        )

  g.connect_by_name( custom_init,  init     )
  g.connect_by_name( custom_lvs,   lvs      )
  g.connect_by_name( custom_power, power    )

  # SRAM macro
  g.connect_by_name( gen_sram, dc             )
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
  g.connect_by_name( gen_sram, gdsmerge       )
  g.connect_by_name( gen_sram, power_gdsmerge )
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
  g.connect_by_name( signoff,        gdsmerge       )
  g.connect_by_name( signoff,        lvs            )
  # Doing DRC on post-fill GDS instead
  #g.connect_by_name( gdsmerge,       drc           )

  g.connect( gdsmerge.o('design_merged.gds'), merge_rdl.i('design.gds') )
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
  g.connect_by_name( dc,       debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( drc,      debugcalibre )
  g.connect_by_name( lvs,      debugcalibre )

  g.connect_by_name( pre_route, route )
  g.connect_by_name( sealring, signoff )
  g.connect_by_name( netlist_fixing, signoff )

  # Post-Power DRC
  g.connect_by_name( power, power_gdsmerge )
  g.connect_by_name( power_gdsmerge, power_drc )
  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

  # DC needs these param to set the NO_CGRA macro
  dc.update_params({'soc_only': parameters['soc_only']}, True)
  # DC needs these params to set macros in soc rtl
  dc.update_params({'TLX_FWD_DATA_LO_WIDTH' : parameters['TLX_FWD_DATA_LO_WIDTH']}, True)
  dc.update_params({'TLX_REV_DATA_LO_WIDTH' : parameters['TLX_REV_DATA_LO_WIDTH']}, True)
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

  # Add sealring at beginning of signoff, so it's in before we stream out GDS
  order = signoff.get_param('order')
  order.insert(0, 'add-sealring.tcl')
  # Add netlist-fixing script before we save new netlist
  index = order.index( 'generate-results.tcl' )
  order.insert( index, 'netlist-fixing.tcl' )
  signoff.update_params( { 'order': order } )

  merge_rdl.update_params( {'coord_x': parameters['dragonphy_rdl_x'], 'coord_y': parameters['dragonphy_rdl_y'], 'flatten_child': True} )

  # Antenna DRC node needs to use antenna rule deck
  antenna_drc.update_params( { 'drc_rule_deck': parameters['antenna_drc_rule_deck'] } )

  # Remove unresolved reference assertion from DC because dragonphy is an unresolved reference
  dc_postconditions = dc.get_postconditions()
  dc_postconditions.remove( "assert 'Unresolved references' not in File( 'logs/dc.log' )" )
  dc_postconditions.remove( "assert 'Unable to resolve' not in File( 'logs/dc.log' )" )
  dc_postconditions.append( """assert "has '1' unresolved references" in File( 'logs/dc.log' )""" )
  dc.set_postconditions( dc_postconditions )
  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()
