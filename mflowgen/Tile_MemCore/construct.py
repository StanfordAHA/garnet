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
  adk_view = 'multicorner-multivt'
  pwr_aware = True

  parameters = {
    'construct_path'      : __file__,
    'design_name'         : 'Tile_MemCore',
    'clock_period'        : 1.1,
    'adk'                 : adk_name,
    'adk_view'            : adk_view,
    # Synthesis
    'flatten_effort'      : 3,
    'topographical'       : True,
    # SRAM macros
    'num_words'           : 512,
    'word_size'           : 32,
    'mux_size'            : 4,
    'corner'              : "tt0p8v25c",
    'bc_corner'           : "ffg0p88v125c",
    'partial_write'       : False,
    # Utilization target
    'core_density_target' : 0.70,
    # RTL Generation
    'interconnect_only'   : True,
    # Power Domains
    'PWR_AWARE'           : pwr_aware

  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl                  = Step( this_dir + '/../common/rtl'                         )
  genlibdb_constraints = Step( this_dir + '/../common/custom-genlibdb-constraints' )
  constraints          = Step( this_dir + '/constraints'                           )
  gen_sram             = Step( this_dir + '/../common/gen_sram_macro'              )
  custom_init          = Step( this_dir + '/custom-init'                           )
  custom_genus_scripts = Step( this_dir + '/custom-genus-scripts'                  )
  custom_flowgen_setup = Step( this_dir + '/custom-flowgen-setup'                  )
  custom_lvs           = Step( this_dir + '/custom-lvs-rules'                      )
  custom_power         = Step( this_dir + '/../common/custom-power-leaf'           )

  # Power aware setup
  if pwr_aware:
      power_domains = Step( this_dir + '/../common/power-domains' )
      pwr_aware_gls = Step( this_dir + '/../common/pwr-aware-gls' )
  # Default steps

  info           = Step( 'info',                           default=True )
  #constraints    = Step( 'constraints',                    default=True )
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
  genlibdb       = Step( 'synopsys-ptpx-genlibdb',         default=True )
  gdsmerge       = Step( 'mentor-calibre-gdsmerge',        default=True )
  drc            = Step( 'mentor-calibre-drc',             default=True )
  lvs            = Step( 'mentor-calibre-lvs',             default=True )
  debugcalibre   = Step( 'cadence-innovus-debug-calibre',  default=True )

  # Extra DC input
  synth.extend_inputs(["common.tcl"])

  # Add sram macro inputs to downstream nodes

  synth.extend_inputs( ['sram_tt.lib', 'sram.lef'] )
  pt_signoff.extend_inputs( ['sram_tt.db'] )
  genlibdb.extend_inputs( ['sram_tt.db'] )

  # These steps need timing and lef info for srams

  sram_steps = \
    [iflow, init, power, place, cts, postcts_hold, route, postroute, postroute_hold, signoff]
  for step in sram_steps:
    step.extend_inputs( ['sram_tt.lib', 'sram_ff.lib', 'sram.lef'] )

  # Need the sram gds to merge into the final layout

  gdsmerge.extend_inputs( ['sram.gds'] )

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

  order = synth.get_param( 'order' )
  order.append( 'copy_sdc.tcl' )
  synth.set_param( 'order', order )


  # Power aware setup
  if pwr_aware:
      synth.extend_inputs(['designer-interface.tcl', 'upf_Tile_MemCore.tcl', 'mem-constraints.tcl', 'mem-constraints-2.tcl', 'dc-dont-use-constraints.tcl'])
      init.extend_inputs(['check-clamp-logic-structure.tcl', 'upf_Tile_MemCore.tcl', 'mem-load-upf.tcl', 'dont-touch-constraints.tcl', 'pd-mem-floorplan.tcl', 'mem-add-endcaps-welltaps-setup.tcl', 'pd-add-endcaps-welltaps.tcl', 'mem-power-switches-setup.tcl', 'add-power-switches.tcl'])
      place.extend_inputs(['check-clamp-logic-structure.tcl', 'place-dont-use-constraints.tcl'])
      power.extend_inputs(['pd-globalnetconnect.tcl'] )
      cts.extend_inputs(['check-clamp-logic-structure.tcl', 'conn-aon-cells-vdd.tcl'])
      postcts_hold.extend_inputs(['check-clamp-logic-structure.tcl', 'conn-aon-cells-vdd.tcl'] )
      route.extend_inputs(['check-clamp-logic-structure.tcl', 'conn-aon-cells-vdd.tcl'] )
      postroute.extend_inputs(['check-clamp-logic-structure.tcl', 'conn-aon-cells-vdd.tcl'] )
      postroute_hold.extend_inputs(['conn-aon-cells-vdd.tcl'] )
      signoff.extend_inputs(['check-clamp-logic-structure.tcl', 'conn-aon-cells-vdd.tcl', 'pd-generate-lvs-netlist.tcl'] )
      pwr_aware_gls.extend_inputs(['design.vcs.pg.v', 'sram_pwr.v'])
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
  g.add_step( pt_signoff   )
  g.add_step( genlibdb_constraints )
  g.add_step( genlibdb             )
  g.add_step( gdsmerge             )
  g.add_step( drc                  )
  g.add_step( lvs                  )
  g.add_step( custom_lvs           )
  g.add_step( debugcalibre         )

  # Power aware step
  if pwr_aware:
      g.add_step( power_domains            )
      g.add_step( pwr_aware_gls            )

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
  g.connect_by_name( adk,      gdsmerge       )
  g.connect_by_name( adk,      drc            )
  g.connect_by_name( adk,      lvs            )

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
  g.connect_by_name( gen_sram,      genlibdb       )
  g.connect_by_name( gen_sram,      pt_signoff     )
  g.connect_by_name( gen_sram,      gdsmerge       )
  g.connect_by_name( gen_sram,      drc            )
  g.connect_by_name( gen_sram,      lvs            )

  g.connect_by_name( rtl,         synth     )
  g.connect_by_name( constraints, synth     )
  g.connect_by_name( custom_genus_scripts, synth )

  g.connect_by_name( synth,       iflow        )
  g.connect_by_name( synth,       init         )
  g.connect_by_name( synth,       power        )
  g.connect_by_name( synth,       place        )
  g.connect_by_name( synth,       cts          )
  g.connect_by_name( custom_flowgen_setup, iflow )

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
  g.connect_by_name( custom_lvs,   lvs      )

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

  g.connect_by_name( signoff,              genlibdb )
  g.connect_by_name( adk,                  genlibdb )
  g.connect_by_name( genlibdb_constraints, genlibdb )

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( synth,    debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( drc,      debugcalibre )
  g.connect_by_name( lvs,      debugcalibre )

  # Pwr aware steps:
  if pwr_aware:
      g.connect_by_name( power_domains,        synth          )
      g.connect_by_name( power_domains,        init           )
      g.connect_by_name( power_domains,        power          )
      g.connect_by_name( power_domains,        place          )
      g.connect_by_name( power_domains,        cts            )
      g.connect_by_name( power_domains,        postcts_hold   )
      g.connect_by_name( power_domains,        route          )
      g.connect_by_name( power_domains,        postroute      )
      g.connect_by_name( power_domains,        postroute_hold )
      g.connect_by_name( power_domains,        signoff        )
      g.connect_by_name( adk,                  pwr_aware_gls)
      g.connect_by_name( gen_sram,             pwr_aware_gls)
      g.connect_by_name( signoff,              pwr_aware_gls)
      #g.connect(power_domains.o('pd-globalnetconnect.tcl'), power.i('globalnetconnect.tcl'))

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  # Update PWR_AWARE variable
  synth.update_params( { 'PWR_AWARE': parameters['PWR_AWARE'] }, True )
  init.update_params( { 'PWR_AWARE': parameters['PWR_AWARE'] }, True )
  power.update_params( { 'PWR_AWARE': parameters['PWR_AWARE'] }, True )

  if pwr_aware:
      pwr_aware_gls.update_params( { 'design_name': parameters['design_name'] }, True )
     
      init.extend_postconditions(         ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )
      place.extend_postconditions(        ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )
      cts.extend_postconditions(          ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )
      postcts_hold.extend_postconditions( ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )
      route.extend_postconditions(        ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )
      postroute.extend_postconditions(    ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )
      signoff.extend_postconditions(      ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )
   

  # Core density target param
  init.update_params( { 'core_density_target': parameters['core_density_target'] }, True )


  # Disable pwr aware flow
  #init.update_params( { 'PWR_AWARE': parameters['PWR_AWARE'] }, allow_new=True )
  #power.update_params( { 'PWR_AWARE': parameters['PWR_AWARE'] }, allow_new=True  )

  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

  # init -- Add 'edge-blockages.tcl' after 'pin-assignments.tcl'

  order = init.get_param('order') # get the default script run order
  path_group_idx = order.index( 'make-path-groups.tcl' ) 
  order.insert( path_group_idx + 1, 'additional-path-groups.tcl' )
  pin_idx = order.index( 'pin-assignments.tcl' ) # find pin-assignments.tcl
  order.insert( pin_idx + 1, 'edge-blockages.tcl' ) # add here
  init.update_params( { 'order': order } )

  # Adding new input for genlibdb node to run
  order = genlibdb.get_param('order') # get the default script run order
  read_idx = order.index( 'read_design.tcl' ) # find read_design.tcl
  order.insert( read_idx + 1, 'genlibdb-constraints.tcl' ) # add here
  genlibdb.update_params( { 'order': order } )


  # Pwr aware steps:
  if pwr_aware:
      # init node
      order = init.get_param('order')
      read_idx = order.index( 'floorplan.tcl' ) # find floorplan.tcl
      order.insert( read_idx + 1, 'mem-load-upf.tcl' ) # add here
      order.insert( read_idx + 2, 'pd-mem-floorplan.tcl' ) # add here
      order.insert( read_idx + 3, 'mem-add-endcaps-welltaps-setup.tcl' ) # add here
      order.insert( read_idx + 4, 'pd-add-endcaps-welltaps.tcl' ) # add here
      order.insert( read_idx + 5, 'mem-power-switches-setup.tcl') # add here
      order.insert( read_idx + 6, 'add-power-switches.tcl' ) # add here
      order.remove('add-endcaps-welltaps.tcl')
      order.append('check-clamp-logic-structure.tcl')
      init.update_params( { 'order': order } )

   # power node
      order = power.get_param('order')
      order.insert( 0, 'pd-globalnetconnect.tcl' ) # add here
      order.remove('globalnetconnect.tcl')
      power.update_params( { 'order': order } )

      # place node
      order = place.get_param('order')
      read_idx = order.index( 'main.tcl' ) # find main.tcl
      order.insert(read_idx - 1, 'place-dont-use-constraints.tcl')
      order.append('check-clamp-logic-structure.tcl')
      place.update_params( { 'order': order } )

      # cts node
      order = cts.get_param('order')
      order.insert( 0, 'conn-aon-cells-vdd.tcl' ) # add here
      order.append('check-clamp-logic-structure.tcl')
      cts.update_params( { 'order': order } )

      # postcts_hold node
      order = postcts_hold.get_param('order')
      order.insert( 0, 'conn-aon-cells-vdd.tcl' ) # add here
      order.append('check-clamp-logic-structure.tcl')
      postcts_hold.update_params( { 'order': order } )

      # route node
      order = route.get_param('order')
      order.insert( 0, 'conn-aon-cells-vdd.tcl' ) # add here
      order.append('check-clamp-logic-structure.tcl')
      route.update_params( { 'order': order } )

      # postroute node
      order = postroute.get_param('order')
      order.insert( 0, 'conn-aon-cells-vdd.tcl' ) # add here
      order.append('check-clamp-logic-structure.tcl')
      postroute.update_params( { 'order': order } )

      # postroute-hold node
      order = postroute_hold.get_param('order')
      order.insert( 0, 'conn-aon-cells-vdd.tcl' ) # add here
      postroute_hold.update_params( { 'order': order } )

      # signoff node
      order = signoff.get_param('order')
      order.insert( 0, 'conn-aon-cells-vdd.tcl' ) # add here
      order.append('check-clamp-logic-structure.tcl')
      read_idx = order.index( 'generate-results.tcl' ) # find generate_results.tcl

      order.insert(read_idx + 1, 'pd-generate-lvs-netlist.tcl')
      signoff.update_params( { 'order': order } )


  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


