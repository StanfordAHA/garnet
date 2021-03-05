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

# Find and import easysteps
# E.g. curdir='/foo/garnet_repo/mflowgen/Tile_PE' => easysteps='../easysteps'
script_dir=os.path.dirname(os.path.realpath(__file__))

sys.path.append(script_dir + '/../esteps2')
from esteps2 import CStep
from esteps2 import DStep
from esteps2 import EStep

from esteps2 import reorder
from esteps2 import econnect
from esteps2 import connect_outstanding_nodes

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

  # 'econnect' allows connections to be declared up here with the step definition.
  # Or: could implement 'AStep' to do the connections all-in-one like CStep etc.
  econnect( adk, 'synth'        )
  econnect( adk, 'iflow'        )
  econnect( adk, 'init'         )
  econnect( adk, 'power'        )
  econnect( adk, 'place'        )
  econnect( adk, 'cts'          )
  econnect( adk, 'postcts_hold' )
  econnect( adk, 'route'        )
  econnect( adk, 'postroute'    )
  econnect( adk, 'signoff'      )
  econnect( adk, 'drc'          )
  econnect( adk, 'lvs'          )
  econnect( adk, 'genlibdb, pt_signoff, debugcalibre' )


  # New alternative CStep() allows step define, add and connect to
  # happen all in one place. In addition, EStep() automatically
  # connects all outputs as successor-node inputs.

  # Custom steps

  rtl                  = CStep( g, '/../common/rtl',              'synth' )
  constraints          = CStep( g, "constraints",                 'synth,iflow' )
  custom_init          = EStep( g, 'custom-init',                 'init' )
  custom_genus_scripts = EStep( g, 'custom-genus-scripts',        'synth'  )
  custom_flowgen_setup = EStep( g, 'custom-flowgen-setup',        'iflow'  )
  custom_power         = EStep( g, '../common/custom-power-leaf', 'power'  )
  short_fix            = EStep( g, '../common/custom-short-fix',  'postroute'  )
  genlibdb_constraints = EStep( g, '../common/custom-genlibdb-constraints', 'genlibdb' )
  custom_timing_assert = EStep( g, '../common/custom-timing-assert',        'synth,postcts_hold,signoff'  )
  custom_dc_scripts    = CStep( g, "custom-dc-scripts",     'iflow' )
  testbench            = CStep( g, "../common/testbench",   'post_pnr_power' )
  application          = CStep( g, "../common/application", 'post_pnr_power,testbench' )

  if synth_power:
    post_synth_power = CStep(g, "../common/tile-post-synth-power", '' )
  post_pnr_power = CStep(g, "../common/tile-post-pnr-power", '' )

  # Power aware setup
  power_domains = None
  pwr_aware_gls = None
  if pwr_aware:
      # Note can still use old-style step declares interleaved with new style.
      power_domains = Step( this_dir + '/../common/power-domains' )
      pwr_aware_gls = Step( this_dir + '/../common/pwr-aware-gls' )

  # Default steps

  # New DStep() allows default-step define, add and connect to happen all in one place.

  info         = DStep( g, 'info', '' )
  synth        = DStep( g, 'cadence-genus-synthesis',     'iflow, init, power, place, cts, custom_flowgen_setup')
  iflow        = DStep( g, 'cadence-innovus-flowsetup',   'init, power, place, cts, postcts_hold, route, postroute, signoff')
  init         = DStep( g, 'cadence-innovus-init',        'power' )
  power        = DStep( g, 'cadence-innovus-power',       'place' )
  place        = DStep( g, 'cadence-innovus-place',       'cts' )
  cts          = DStep( g, 'cadence-innovus-cts',         'postcts_hold' )
  postcts_hold = DStep( g, 'cadence-innovus-postcts_hold','route' )
  route        = DStep( g, 'cadence-innovus-route',       'postroute' )
  postroute    = DStep( g, 'cadence-innovus-postroute',   'signoff' )
  signoff      = DStep( g, 'cadence-innovus-signoff',     'drc, lvs, genlibdb, post_pnr_power, pt_signoff')
  pt_signoff   = DStep( g, 'synopsys-pt-timing-signoff',  'post_pnr_power' )
  genlibdb     = DStep( g, 'cadence-genus-genlib',        '' )

  if which("calibre") is not None:
      drc          = Step( 'mentor-calibre-drc',            default=True )
      lvs          = Step( 'mentor-calibre-lvs',            default=True )
  else:
      drc          = Step( 'cadence-pegasus-drc',           default=True )
      lvs          = Step( 'cadence-pegasus-lvs',           default=True )
  debugcalibre = Step( 'cadence-innovus-debug-calibre', default=True )

  # Add custom timing scripts
  # (No longer needed because done by EStep() above)

  # Add extra input edges to innovus steps that need custom tweaks
  # (No longer needed because done by EStep() above)

  # Extra input to DC for constraints
  synth.extend_inputs( ["common.tcl", "reporting.tcl", "generate-results.tcl", "scenarios.tcl", "report_alu.py", "parse_alu.py"] )
  # Extra outputs from DC
  synth.extend_outputs( ["sdc"] )
  iflow.extend_inputs( ["scenarios.tcl", "sdc"] )
  init.extend_inputs( ["sdc"] )
  power.extend_inputs( ["sdc"] )
  place.extend_inputs( ["sdc"] )
  cts.extend_inputs( ["sdc"] )

  # New 'reorder()' method simplifies this common task...
  # Or: could e.g. implement something more generic like
  #    modify_parmlist( synth, 'order', 'last: copy_sdc.tcl' )
  reorder( synth, 'last: copy_sdc.tcl' )

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

  # (Can still do old-style add_step() if desired)

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

  # I guess...this is another way to do extend_inputs/outputs()?
  g.connect( signoff.o('design-merged.gds'), drc.i('design_merged.gds') )
  g.connect( signoff.o('design-merged.gds'), lvs.i('design_merged.gds') )


  # Old-style connect syntax still allowed...
  if synth_power:
      g.connect_by_name( application, post_synth_power )
      g.connect_by_name( synth,       post_synth_power )
      g.connect_by_name( testbench,   post_synth_power )

  # Old-style connect syntax still allowed...
  g.connect_by_name( synth,    debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( drc,      debugcalibre )
  g.connect_by_name( lvs,      debugcalibre )

  # Pwr aware steps (old-style syntax):
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
    reorder( c_step, 'last: report-special-timing.tcl' )
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

  reorder(init,
          'after make-path-groups.tcl : additional-path-groups.tcl',
          'after pin-assignments.tcl  : edge-blockages.tcl')

  # Adding new input for genlibdb node to run
  reorder( genlibdb, 'after read_design.tcl : genlibdb-constraints.tcl' )

  # Pwr aware steps:
  if pwr_aware:

      # init node
      reorder(init,
              'after floorplan.tcl: pe-load-upf.tcl',
              'then  : pd-pe-floorplan.tcl',
              'then  : pe-add-endcaps-welltaps-setup.tcl',
              'then  : pd-add-endcaps-welltaps.tcl',
              'then  : pe-power-switches-setup.tcl',
              'then  : add-power-switches.tcl',
              'remove: add-endcaps-welltaps.tcl',
              'last  : check-clamp-logic-structure.tcl')

      # power node
      reorder(power,
              'first : pd-globalnetconnect.tcl',
              'delete: globalnetconnect.tcl')

      # place node
      reorder(place,
              'after  main.tcl: add-aon-tie-cells.tcl',
              'before main.tcl: place-dont-use-constraints.tcl',
              'last           : check-clamp-logic-structure.tcl')

      # cts node
      reorder(cts,
              'first: conn-aon-cells-vdd.tcl',
              'last:  check-clamp-logic-structure.tcl')

      # postcts_hold node
      reorder(postcts_hold,
              'first: conn-aon-cells-vdd.tcl',
              'last:  check-clamp-logic-structure.tcl')

      # route node
      reorder(route,
              'first: conn-aon-cells-vdd.tcl',
              'last:  check-clamp-logic-structure.tcl')

      # postroute node
      reorder(postroute,
              'first: conn-aon-cells-vdd.tcl',
              'last:  check-clamp-logic-structure.tcl')

      # Add fix-shorts as the last thing to do in postroute
      reorder(postroute, 'last:  fix-shorts.tcl')

      # signoff node
      reorder(signoff,
              'first                     : conn-aon-cells-vdd.tcl',
              'after generate-results.tcl: pd-generate-lvs-netlist.tcl',
              'last                      : check-clamp-logic-structure.tcl')
  return g

if __name__ == '__main__':
  g = construct()
  # g.plot()


