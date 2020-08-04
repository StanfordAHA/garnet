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
    'construct_path'    : __file__,
    'design_name'       : 'Tile_PE',
    'clock_period'      : 1.1,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    # Synthesis
    'flatten_effort'    : 3,
    'topographical'     : True,
    # RTL Generation
    'interconnect_only' : True,
    # Power Domains
    'PWR_AWARE'         : pwr_aware
  
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
  constraints          = Step( this_dir + '/constraints'                           )
  custom_init          = Step( this_dir + '/custom-init'                           )
  custom_power         = Step( this_dir + '/../common/custom-power-leaf'           )
  genlibdb_constraints = Step( this_dir + '/../common/custom-genlibdb-constraints' )
  custom_timing_assert = Step( this_dir + '/../common/custom-timing-assert'        )
  custom_dc_scripts    = Step( this_dir + '/custom-dc-scripts'                     )
  iflow                = Step( this_dir + '/cadence-innovus-flowsetup'             )

  # Power aware setup
  if pwr_aware: 
      power_domains = Step( this_dir + '/../common/power-domains' )
      pwr_aware_gls = Step( this_dir + '/../common/pwr-aware-gls' )
  # Default steps

  info         = Step( 'info',                          default=True )
  #constraints  = Step( 'constraints',                   default=True )
  dc           = Step( 'synopsys-dc-synthesis',         default=True )
  #iflow        = Step( 'cadence-innovus-flowsetup',     default=True )
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

  # Add custom timing scripts

  custom_timing_steps = [ dc, postcts_hold, signoff ] # connects to these
  for c_step in custom_timing_steps:
    c_step.extend_inputs( custom_timing_assert.all_outputs() )

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )
  genlibdb.extend_inputs( genlibdb_constraints.all_outputs() )

  # Extra input to DC for constraints
  dc.extend_inputs( ["common.tcl", "reporting.tcl", "generate-results.tcl", "scenarios.tcl", "report_alu.py", "parse_alu.py"] )
  # Extra outputs from DC
  dc.extend_outputs( ["sdc"] )
  iflow.extend_inputs( ["scenarios.tcl", "sdc"] )
  init.extend_inputs( ["sdc"] )
  power.extend_inputs( ["sdc"] )
  place.extend_inputs( ["sdc"] )
  cts.extend_inputs( ["sdc"] )

  # Power aware setup
  if pwr_aware: 
      dc.extend_inputs(['designer-interface.tcl', 'upf_Tile_PE.tcl', 'pe-constraints.tcl', 'pe-constraints-2.tcl', 'dc-dont-use-constraints.tcl'])
      init.extend_inputs(['upf_Tile_PE.tcl', 'pe-load-upf.tcl', 'dont-touch-constraints.tcl', 'pd-pe-floorplan.tcl', 'pe-add-endcaps-welltaps-setup.tcl', 'pd-add-endcaps-welltaps.tcl', 'pe-power-switches-setup.tcl', 'add-power-switches.tcl', 'check-clamp-logic-structure.tcl'])
      place.extend_inputs(['place-dont-use-constraints.tcl', 'check-clamp-logic-structure.tcl'])
      power.extend_inputs(['pd-globalnetconnect.tcl'] )
      cts.extend_inputs(['conn-aon-cells-vdd.tcl', 'check-clamp-logic-structure.tcl'])
      postcts_hold.extend_inputs(['conn-aon-cells-vdd.tcl', 'check-clamp-logic-structure.tcl'] )
      route.extend_inputs(['conn-aon-cells-vdd.tcl', 'check-clamp-logic-structure.tcl'] ) 
      postroute.extend_inputs(['conn-aon-cells-vdd.tcl', 'check-clamp-logic-structure.tcl'] )
      signoff.extend_inputs(['conn-aon-cells-vdd.tcl', 'pd-generate-lvs-netlist.tcl', 'check-clamp-logic-structure.tcl'] ) 
      pwr_aware_gls.extend_inputs(['design.vcs.pg.v']) 

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info                     )
  g.add_step( rtl                      )
  g.add_step( constraints              )
  g.add_step( custom_dc_scripts        )
  g.add_step( dc                       )
  g.add_step( custom_timing_assert     )
  g.add_step( iflow                    )
  g.add_step( init                     )
  g.add_step( custom_init              )
  g.add_step( power                    )
  g.add_step( custom_power             )
  g.add_step( place                    )
  g.add_step( cts                      )
  g.add_step( postcts_hold             )
  g.add_step( route                    )
  g.add_step( postroute                )
  g.add_step( signoff                  )
  g.add_step( pt_signoff   )
  g.add_step( genlibdb_constraints     )
  g.add_step( genlibdb                 )
  g.add_step( gdsmerge                 )
  g.add_step( drc                      )
  g.add_step( lvs                      )
  g.add_step( debugcalibre             )

  # Power aware step
  if pwr_aware:
      g.add_step( power_domains            )
      g.add_step( pwr_aware_gls            )

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

  g.connect_by_name( rtl,         dc        )
  g.connect_by_name( constraints, dc        )
  g.connect_by_name( custom_dc_scripts, dc  )
  g.connect_by_name( constraints, iflow     )
  g.connect_by_name( custom_dc_scripts, iflow)

  for c_step in custom_timing_steps:
    g.connect_by_name( custom_timing_assert, c_step )

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

  g.connect_by_name( signoff,              genlibdb )
  g.connect_by_name( adk,                  genlibdb )
  g.connect_by_name( genlibdb_constraints, genlibdb )

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( dc,       debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( drc,      debugcalibre )
  g.connect_by_name( lvs,      debugcalibre )

  # Pwr aware steps:
  if pwr_aware: 
      g.connect_by_name( power_domains,        dc           )
      g.connect_by_name( power_domains,        init         ) 
      g.connect_by_name( power_domains,        power        )
      g.connect_by_name( power_domains,        place        )
      g.connect_by_name( power_domains,        cts          )
      g.connect_by_name( power_domains,        postcts_hold )
      g.connect_by_name( power_domains,        route        )
      g.connect_by_name( power_domains,        postroute    )
      g.connect_by_name( power_domains,        signoff      )
      g.connect_by_name( adk,                  pwr_aware_gls)
      g.connect_by_name( signoff,              pwr_aware_gls)
      #g.connect(power_domains.o('pd-globalnetconnect.tcl'), power.i('globalnetconnect.tcl'))
  
  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  # Add custom timing scripts

  for c_step in custom_timing_steps:
    order = c_step.get_param( 'order' )
    order.append( 'report-special-timing.tcl' )
    c_step.set_param( 'order', order )
    c_step.extend_postconditions( [{ 'pytest': 'inputs/test_timing.py' }] )

  # Update PWR_AWARE variable
  dc.update_params( { 'PWR_AWARE': parameters['PWR_AWARE'] }, True )
  init.update_params( { 'PWR_AWARE': parameters['PWR_AWARE'] }, True )
  power.update_params( { 'PWR_AWARE': parameters['PWR_AWARE'] }, True )
 
  if pwr_aware:
     init.update_params( { 'flatten_effort': parameters['flatten_effort'] }, True ) 
     pwr_aware_gls.update_params( { 'design_name': parameters['design_name'] }, True ) 
     
     init.extend_postconditions(         ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )  
     place.extend_postconditions(        ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )
     cts.extend_postconditions(          ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )
     postcts_hold.extend_postconditions( ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )
     route.extend_postconditions(        ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )
     postroute.extend_postconditions(    ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )
     signoff.extend_postconditions(      ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"] )
  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

  # init -- Add 'edge-blockages.tcl' after 'pin-assignments.tcl'
  # and 'additional-path-groups' after 'make_path_groups'

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
      order.insert( read_idx + 1, 'pe-load-upf.tcl' ) # add here
      order.insert( read_idx + 2, 'pd-pe-floorplan.tcl' ) # add here
      order.insert( read_idx + 3, 'pe-add-endcaps-welltaps-setup.tcl' ) # add here
      order.insert( read_idx + 4, 'pd-add-endcaps-welltaps.tcl' ) # add here
      order.insert( read_idx + 5, 'pe-power-switches-setup.tcl') # add here
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

      # signoff node
      order = signoff.get_param('order')
      order.insert( 0, 'conn-aon-cells-vdd.tcl' ) # add here 
      read_idx = order.index( 'generate-results.tcl' ) # find generate_results.tcl 
      order.insert(read_idx + 1, 'pd-generate-lvs-netlist.tcl')
      order.append('check-clamp-logic-structure.tcl')
      signoff.update_params( { 'order': order } )

  return g

if __name__ == '__main__':
  g = construct()
#  g.plot()


