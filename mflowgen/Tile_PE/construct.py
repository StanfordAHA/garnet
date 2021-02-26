#! /usr/bin/env python
#=========================================================================
# construct.py
#=========================================================================
# Author :
# Date   :
#

import os
import sys
from shutil import which

from mflowgen.components import Graph, Step

# Find and import easysteps
# E.g. curdir='/foo/garnet_repo/mflowgen/Tile_PE' => easysteps='../easysteps'
script_dir=os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_dir + '/../easysteps')

from easysteps import extend_steps
from easysteps import add_custom_steps
from easysteps import add_default_steps
from easysteps import connect_outstanding_nodes

def construct():

  g = Graph()

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  adk_name = 'tsmc16'
  adk_view = 'multicorner-multivt'
  pwr_aware = True

  flatten = 3
  if os.environ.get('FLATTEN'):
      flatten = os.environ.get('FLATTEN')

  synth_power = False
  if os.environ.get('SYNTH_POWER') == 'True':
      synth_power = True
  # power domains do not work with post-synth power
  if synth_power:
      pwr_aware = False

  parameters = {
    'construct_path'    : __file__,
    'design_name'       : 'Tile_PE',
    'clock_period'      : 1.1,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    # Synthesis
    'flatten_effort'    : flatten,
    'topographical'     : True,
    # RTL Generation
    'interconnect_only' : True,
    # Power Domains
    'PWR_AWARE'         : pwr_aware,
    'core_density_target': 0.63,
    # Power analysis
    "use_sdf"           : False, # uses sdf but not the way it is in xrun node
    'app_to_run'        : 'tests/conv_3_3',
    'saif_instance'     : 'testbench/dut',
    'testbench_name'    : 'testbench',
    'strip_path'        : 'testbench/dut'
    }

  # steveri 2101: Hoping this is temporary.
  # But for now, 1.1ns pe tile is too big and full-chip CI test FAILS
  if (os.getenv('USER') == "buildkite-agent"):
      parameters['clock_period'] = 4.0; # 4ns = 250 MHz

  # User-level option to change clock frequency
  # E.g. 'export clock_period_PE="4.0"' to target 250MHz
  # Optionally could restrict to bk only: if (os.getenv('USER') == "buildkite-agent")
  cp=os.getenv('clock_period_PE')
  if (cp != None):
      print("@file_info: WARNING found env var 'clock_period_PE'")
      print("@file_info: WARNING setting PE clock period to '%s'" % cp)
      parameters['clock_period'] = cp;

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  add_custom_steps(g, """

        rtl                - ../common/rtl                  -> synth
        constraints        - constraints                    -> synth iflow
        custom_dc_scripts  - custom-dc-scripts              -> iflow
        testbench          - ../common/testbench            -> post_pnr_power
        application        - ../common/application          -> post_pnr_power testbench
        post_pnr_power     - ../common/tile-post-pnr-power

  """, DBG=1)

  if synth_power:
    add_custom_steps(g, "post_synth_power ../common/tile-post-synth-power")


  # Extension steps (steps that connect *all* outputs to each successor node)

  extend_steps(g, """

    # Add extra input edges to innovus steps that need custom tweaks
    custom_init          - custom-init                           -> init
    custom_power         - ../common/custom-power-leaf           -> power
    custom_genus_scripts - custom-genus-scripts                  -> synth
    custom_flowgen_setup - custom-flowgen-setup                  -> iflow
    genlibdb_constraints - ../common/custom-genlibdb-constraints -> genlibdb

    # Provides script for fixing shorts caused by steps up to and including postroute
    short_fix - ../common/custom-short-fix -> postroute

    # Add custom timing scripts
    custom_timing_assert - ../common/custom-timing-assert -> synth postcts_hold signoff

  """, DBG=1)

  # Power aware setup
  power_domains = None
  pwr_aware_gls = None
  if pwr_aware:
      power_domains = Step( this_dir + '/../common/power-domains' )
      pwr_aware_gls = Step( this_dir + '/../common/pwr-aware-gls' )

  # Default steps

  add_default_steps(g, """
    info         - info
    init         - cadence-innovus-init          -> power
    power        - cadence-innovus-power         -> place
    place        - cadence-innovus-place         -> cts
    cts          - cadence-innovus-cts           -> postcts_hold
    postcts_hold - cadence-innovus-postcts_hold  -> route
    route        - cadence-innovus-route         -> postroute
    postroute    - cadence-innovus-postroute     -> signoff
    pt_signoff   - synopsys-pt-timing-signoff    -> post_pnr_power
    genlibdb     - cadence-genus-genlib
  """, DBG=1)

  add_default_steps(g, """
    synth   - cadence-genus-synthesis       
            -> iflow init power place cts custom_flowgen_setup

    iflow   - cadence-innovus-flowsetup     
            -> init power place cts postcts_hold route postroute signoff

    signoff - cadence-innovus-signoff       
            -> drc lvs genlibdb post_pnr_power pt_signoff
  """)

  if which("calibre") is not None:
      drc          = Step( 'mentor-calibre-drc',            default=True )
      lvs          = Step( 'mentor-calibre-lvs',            default=True )
  else:
      drc          = Step( 'cadence-pegasus-drc',           default=True )
      lvs          = Step( 'cadence-pegasus-lvs',           default=True )
  debugcalibre = Step( 'cadence-innovus-debug-calibre', default=True )


  # Extra input to DC for constraints
  synth.extend_inputs( ["common.tcl", "reporting.tcl", "generate-results.tcl", "scenarios.tcl", "report_alu.py", "parse_alu.py"] )
  # Extra outputs from DC
  synth.extend_outputs( ["sdc"] )
  iflow.extend_inputs( ["scenarios.tcl", "sdc"] )
  init.extend_inputs( ["sdc"] )
  power.extend_inputs( ["sdc"] )
  place.extend_inputs( ["sdc"] )
  cts.extend_inputs( ["sdc"] )

  order = synth.get_param( 'order' )
  order.append( 'copy_sdc.tcl' )
  synth.set_param( 'order', order )

  # Power aware setup
  if pwr_aware:
      synth.extend_inputs(['designer-interface.tcl', 'upf_Tile_PE.tcl', 'pe-constraints.tcl', 'pe-constraints-2.tcl', 'dc-dont-use-constraints.tcl'])
      init.extend_inputs(['upf_Tile_PE.tcl', 'pe-load-upf.tcl', 'dont-touch-constraints.tcl', 'pd-pe-floorplan.tcl', 'pe-add-endcaps-welltaps-setup.tcl', 'pd-add-endcaps-welltaps.tcl', 'pe-power-switches-setup.tcl', 'add-power-switches.tcl', 'check-clamp-logic-structure.tcl'])
      power.extend_inputs(['pd-globalnetconnect.tcl'] )
      place.extend_inputs(['place-dont-use-constraints.tcl', 'check-clamp-logic-structure.tcl', 'add-aon-tie-cells.tcl'])
      cts.extend_inputs(['conn-aon-cells-vdd.tcl', 'check-clamp-logic-structure.tcl'])
      postcts_hold.extend_inputs(['conn-aon-cells-vdd.tcl', 'check-clamp-logic-structure.tcl'] )
      route.extend_inputs(['conn-aon-cells-vdd.tcl', 'check-clamp-logic-structure.tcl'] )
      postroute.extend_inputs(['conn-aon-cells-vdd.tcl', 'check-clamp-logic-structure.tcl'] )
      signoff.extend_inputs(['conn-aon-cells-vdd.tcl', 'pd-generate-lvs-netlist.tcl', 'check-clamp-logic-structure.tcl'] )
      pwr_aware_gls.extend_inputs(['design.vcs.pg.v'])
  
  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( drc                      )
  g.add_step( lvs                      )
  g.add_step( debugcalibre             )

  if synth_power:
    g.add_step( post_synth_power       )

  # Power aware step
  if pwr_aware:
      g.add_step( power_domains        )
      g.add_step( pwr_aware_gls        )
                      
  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Dynamically add edges

  # Complete all easysteps connections
  connect_outstanding_nodes(g, DBG=1)

  # Connect by name

  g.connect_by_name( adk,      synth        )
  g.connect_by_name( adk,      iflow        )
  g.connect_by_name( adk,      init         )
  g.connect_by_name( adk,      power        )
  g.connect_by_name( adk,      place        )
  g.connect_by_name( adk,      cts          )
  g.connect_by_name( adk,      postcts_hold )
  g.connect_by_name( adk,      route        )
  g.connect_by_name( adk,      postroute    )
  g.connect_by_name( adk,      signoff      )
  g.connect_by_name( adk,      drc          )
  g.connect_by_name( adk,      lvs          )

  g.connect(signoff.o('design-merged.gds'), drc.i('design_merged.gds'))
  g.connect(signoff.o('design-merged.gds'), lvs.i('design_merged.gds'))

  g.connect_by_name( adk,          genlibdb )
  g.connect_by_name( adk,          pt_signoff   )

  if synth_power:
      g.connect_by_name( application, post_synth_power )
      g.connect_by_name( synth,       post_synth_power )
      g.connect_by_name( testbench,   post_synth_power )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( synth,    debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( drc,      debugcalibre )
  g.connect_by_name( lvs,      debugcalibre )

  # Pwr aware steps:
  if pwr_aware:
      g.connect_by_name( power_domains,        synth        )
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

  custom_timing_steps = [ synth, postcts_hold, signoff ] # connects to these
  for c_step in custom_timing_steps:
    order = c_step.get_param( 'order' )
    order.append( 'report-special-timing.tcl' )
    c_step.set_param( 'order', order )
    c_step.extend_postconditions( [{ 'pytest': 'inputs/test_timing.py' }] )

  # Update PWR_AWARE variable
  synth.update_params( { 'PWR_AWARE': parameters['PWR_AWARE'] }, True )
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

  init.update_params( { 'core_density_target': parameters['core_density_target'] }, True )
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
      order.insert(read_idx + 1, 'add-aon-tie-cells.tcl')
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

      # Add fix-shorts as the last thing to do in postroute
      order = postroute.get_param('order') ; # get the default script run order
      order.append('fix-shorts.tcl' )      ; # Add fix-shorts at the end
      postroute.update_params( { 'order': order } ) ; # Update

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
  # g.plot()


