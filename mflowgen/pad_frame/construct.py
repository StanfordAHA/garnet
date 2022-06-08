#! /usr/bin/env python
#=========================================================================
# construct.py
#=========================================================================

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

  adk_name = get_sys_adk()
  adk_view = 'view-standard'

  parameters = {
    'construct_path'    : __file__,
    'design_name'       : 'GarnetSOC_pad_frame',
    'clock_period'      : 20.0,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    # soc-rtl
    'include_core'      : 0,
    # Synthesis
    'flatten_effort'    : 3,
    'topographical'     : False,
    'express_flow'      : False,
    'skip_verify_connectivity' : True,
    'lvs_hcells_file' : 'inputs/adk/hcells.inc',
    'lvs_connect_names' : '"VDD VSS VDDPST"'
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step
  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps
  soc_rtl              = Step( this_dir + '/../common/soc-rtl-v2'                )
  rtl                  = Step( this_dir + '/rtl'                         )   
  constraints          = Step( this_dir + '/constraints'                 )
  init_fullchip        = Step( this_dir + '/../common/init-fullchip'     )
  netlist_fixing       = Step( this_dir + '/../common/fc-netlist-fixing' )

  # Custom step 'pre-flowsetup'
  # To get new lef cells e.g. 'icovl-cells.lef' into iflow, we gotta:
  # - create new step 'pre_flowsetup' whose outputs are icovl cells
  # -- link via "commands" group in pre-iflow/configure.yml
  # - connect pre-flowsetup step to flowsetup (iflow) step
  # - extend iflow inputs to include icovl cells
  # - iflow "setup.tcl" automatically includes "inputs/*.lef"
  pre_flowsetup         = Step( this_dir + '/pre-flowsetup'        )

  # More custom steps
  custom_power         = Step( this_dir + '/../common/custom-power-chip' )

  # It's not plugged in yet!
  # custom_power         = Step( this_dir + '/custom-power'                )

  # Some kinda primetime thingy maybe
  # genlibdb_constraints = Step( this_dir + '/../common/custom-genlibdb-constraints' )

  # Default steps
  info         = Step( 'info',                          default=True )
  # constraints= Step( 'constraints',                   default=True )
  dc           = Step( 'synopsys-dc-synthesis',         default=True )
  iflow        = Step( 'cadence-innovus-flowsetup',     default=True )
  init         = Step( 'cadence-innovus-init',          default=True )
  power        = Step( 'cadence-innovus-power',         default=True )
  place        = Step( 'cadence-innovus-place',         default=True )
  route        = Step( 'cadence-innovus-route',         default=True )
  signoff      = Step( 'cadence-innovus-signoff',       default=True )
  pt_signoff   = Step( 'synopsys-pt-timing-signoff',    default=True )
  genlibdb     = Step( 'synopsys-ptpx-genlibdb',        default=True )
  init_fill    = Step( 'mentor-calibre-fill',           default=True )
  if which("calibre") is not None:
      drc          = Step( 'mentor-calibre-drc',            default=True )
      lvs          = Step( 'mentor-calibre-lvs',            default=True )
  else:
      drc          = Step( 'cadence-pegasus-drc',           default=True )
      lvs          = Step( 'cadence-pegasus-lvs',           default=True )
  debugcalibre = Step( 'cadence-innovus-debug-calibre', default=True )

  # Die if unconnected bumps (why was this deleted?)
  init.extend_postconditions([
    "assert 'STILL UNCONNECTED: bump' not in File( 'mflowgen-run.log' )"
  ])

  # Send in the clones
  # 'init' step now gets its own design-rule check
  init_drc = drc.clone()
  init_drc.set_name( 'init-drc' )

  #-----------------------------------------------------------------------
  # Add extra input edges to innovus steps that need custom tweaks
  #-----------------------------------------------------------------------

  # "init" (cadence-innovus-init) inputs are "init_fullchip" outputs
  init.extend_inputs( init_fullchip.all_outputs() )

  # Also: 'init' now produces a gds file
  # for intermediate drc check 'init-drc'
  init.extend_outputs( ["design-merged.gds"] )
  
  # "power" inputs are "custom_power" outputs
  power.extend_inputs( custom_power.all_outputs() )

  signoff.extend_inputs( netlist_fixing.all_outputs() )

  # Your comment here.
  # FIXME what about gds???
  # iflow (flowsetup) setup.tcl includes all files inputs/*.lef maybe
  # iflow.extend_inputs( [ "icovl-cells.lef" , "dtcd-cells.lef" ] )

  # genlibdb.extend_inputs( genlibdb_constraints.all_outputs() )

  # Ouch. iflow and everyone that connects to iflow must also include
  # the icovl/dtcd lefs I guess?
  pre_flowsetup_followers = [
    # iflow, init, power, place, cts, postcts_hold, route, postroute, signoff
    iflow, init # can we get away with this?
  ]
  for step in pre_flowsetup_followers:
    step.extend_inputs( [ 
      "icovl-cells.lef", "dtcd-cells.lef", 
      "bumpcells.lef" 
    ] )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info                     )
  g.add_step( soc_rtl                  )
  g.add_step( rtl                      )
  g.add_step( constraints              )
  g.add_step( dc                       )

  # pre_flowsetup => iflow
  g.add_step( pre_flowsetup            )
  g.add_step( iflow                    )
  g.add_step( init_fullchip            )
  g.add_step( init                     )

  g.add_step( init_fill                )
  g.add_step( init_drc                 )

  g.add_step( power                    )
  g.add_step( custom_power             )
  g.add_step( place                    )
  g.add_step( route                    )
  g.add_step( netlist_fixing           )
  g.add_step( signoff                  )
  g.add_step( pt_signoff   )
  # g.add_step( genlibdb_constraints     )
  g.add_step( genlibdb                 )
  g.add_step( drc                      )
  g.add_step( lvs                      )
  g.add_step( debugcalibre             )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( adk,      dc            )
  g.connect_by_name( adk,      pre_flowsetup )
  g.connect_by_name( adk,      iflow         )
  g.connect_by_name( adk,      init          )
  g.connect_by_name( adk,      init_fill     )
  g.connect_by_name( adk,      init_drc      )
  g.connect_by_name( adk,      power         )
  g.connect_by_name( adk,      place         )
  g.connect_by_name( adk,      route         )
  g.connect_by_name( adk,      signoff       )
  g.connect_by_name( adk,      drc           )
  g.connect_by_name( adk,      lvs           )

  g.connect_by_name( soc_rtl, rtl )

  g.connect_by_name( rtl,         dc        )
  g.connect_by_name( constraints, dc        )

  # sr02.2020 b/c now init_fullchip needs io_file from soc-rtl
  g.connect_by_name( soc_rtl,  init_fullchip )

  g.connect_by_name( dc,       iflow        )
  g.connect_by_name( dc,       init         )
  g.connect_by_name( dc,       power        )
  g.connect_by_name( dc,       place        )

  # g.connect_by_name( pre_flowsetup,  iflow   )
  # iflow, init, power, place, cts, postcts_hold, route, postroute, signoff
  for step in pre_flowsetup_followers:
    g.connect_by_name( pre_flowsetup, step)

  g.connect_by_name( iflow,    init         )
  g.connect_by_name( iflow,    power        )
  g.connect_by_name( iflow,    place        )
  g.connect_by_name( iflow,    route        )
  g.connect_by_name( iflow,    signoff      )
  # for step in iflow_followers:
  #   g.connect_by_name( iflow, step)

  g.connect_by_name( init_fullchip, init   )
  g.connect_by_name( custom_power,  power  )

  # init => init_drc
  g.connect( init.o('design-merged.gds'), init_drc.i('design_merged.gds') )
  g.connect( init.o('design-merged.gds'), init_fill.i('design.gds') )

  g.connect_by_name( init,         power        )
  g.connect_by_name( power,        place        )
  g.connect_by_name( place,        route        )
  g.connect_by_name( route,        signoff      )
  g.connect_by_name( signoff,      drc          )
  g.connect_by_name( signoff,      lvs          )
  g.connect( signoff.o('design-merged.gds'), drc.i('design_merged.gds') )
  g.connect( signoff.o('design-merged.gds'), lvs.i('design_merged.gds') )

  g.connect_by_name( signoff,              genlibdb )
  g.connect_by_name( adk,                  genlibdb )
#   g.connect_by_name( genlibdb_constraints, genlibdb )

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( dc,       debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( drc,      debugcalibre )
  g.connect_by_name( lvs,      debugcalibre )

  # Netlist fixing should be run during signoff
  g.connect_by_name( netlist_fixing, signoff )

  # yes? no?
  # g.connect_by_name( init_drc,      debugcalibre )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------
  g.update_params( parameters )

  # Default order can be found in e.g.
  # mflowgen/steps/cadence-innovus-init/configure.yml
  #     - main.tcl
  #     - quality-of-life.tcl
  #     - floorplan.tcl
  #     - pin-assignments.tcl
  #     - make-path-groups.tcl
  #     - reporting.tcl

  # I copied this from someone else, maybe glb_top or something
  # Looks like this order deletes pin assignments and adds endcaps/welltaps
  # then maybe get clean(er) post-floorplan drc
  #
  # ?? moved stream-out to *before* alignment-cells so to get pre-icovl gds
  # FIXME does this mean we're not checking bump-route DRC?

  # Note "route-phy-bumps" explicitly sources a file "analog-bumps/build-phy-nets.tcl"
  # 5/2020 moved stream-out to *after* bump routing
  init.update_params(
    {'order': [
      'main.tcl','quality-of-life.tcl',
      'stylus-compatibility-procs.tcl','floorplan.tcl','io-fillers.tcl',
      'attach-results-to-outputs.tcl',
      'alignment-cells.tcl',
      'analog-bumps/route-phy-bumps.tcl', 
      'analog-bumps/bump-connect.tcl',
      'gen-bumps.tcl', 'check-bumps.tcl', 'route-bumps.tcl',
      'innovus-foundation-flow/custom-scripts/stream-out.tcl',
    ]}
  )

  order = power.get_param('order')
  order.append( 'add-endcaps-welltaps.tcl' )
  power.update_params( { 'order': order } )
 
  # Signoff Order 
  order = signoff.get_param('order')
  index = order.index( 'generate-results.tcl' ) # Fix netlist before streaming out netlist
  order.insert( index, 'netlist-fixing.tcl' )
  signoff.update_params( { 'order': order } )

  # Not sure what this is or why it was commented out...
  #   # Adding new input for genlibdb node to run 
  #   genlibdb.update_params(
  #     {'order': "\"read_design.tcl genlibdb-constraints.tcl extract_model.tcl\""}
  #   )

  return g


if __name__ == '__main__':
  g = construct()
  # g.plot()
