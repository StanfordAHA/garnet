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
    'design_name'         : 'Tile_PE',
    'clock_period'        : 1.1 * 1000,
    'core_density_target' : 0.6,
    'adk'                 : adk_name,
    'adk_view'            : adk_view,
    'adk_stdcell'         : 'b15_7t_108pp',
    # Synthesis
    'flatten_effort'      : 3,
    'topographical'       : True,
    'read_hdl_defines'    : read_hdl_defines,
    # RTL Generation
    'interconnect_only'   : False,
    'rtl_docker_image'    : 'default', # Current default is 'stanfordaha/garnet:latest'
    # Timing Slack
    'setup_target_slack'  : 0,
    'hold_target_slack'   : 0.015,
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
  # rtl                = Step( this_dir + '/../common/rtl'                          )
  rtl                  = Step( this_dir + '/../common/rtl-cache'                    )
  constraints          = Step( this_dir + '/constraints'                            )
  custom_init          = Step( this_dir + '/custom-init'                            )
  custom_genus_scripts = Step( this_dir + '/custom-genus-scripts'                   )
  custom_flowgen_setup = Step( this_dir + '/custom-flowgen-setup'                   )
  custom_power         = Step( this_dir + '/../common/custom-power-leaf'            )
  custom_cts           = Step( this_dir + '/custom-cts'                             )
  genlibdb_constraints = Step( this_dir + '/../common/custom-genlibdb-constraints'  )
  custom_timing_assert = Step( this_dir + '/../common/custom-timing-assert'         )
  custom_dc_scripts    = Step( this_dir + '/custom-dc-scripts'                      )
  testbench            = Step( this_dir + '/../common/testbench'                    )
  application          = Step( this_dir + '/../common/application'                  )
  lib2db               = Step( this_dir + '/../common/synopsys-dc-lib2db'           )
  post_pnr_power       = Step( this_dir + '/../common/tile-post-pnr-power'          )
  drc                  = Step( this_dir + '/../common/intel16-synopsys-icv-drc'     )
  lvs                  = Step( this_dir + '/../common/intel16-synopsys-icv-lvs'     )

  # Default steps
  info           = Step( 'info',                          default=True )
  synth          = Step( 'cadence-genus-synthesis',       default=True )
  iflow          = Step( 'cadence-innovus-flowsetup',     default=True )
  init           = Step( 'cadence-innovus-init',          default=True )
  power          = Step( 'cadence-innovus-power',         default=True )
  place          = Step( 'cadence-innovus-place',         default=True )
  cts            = Step( 'cadence-innovus-cts',           default=True )
  postcts_hold   = Step( 'cadence-innovus-postcts_hold',  default=True )
  route          = Step( 'cadence-innovus-route',         default=True )
  postroute      = Step( 'cadence-innovus-postroute',     default=True )
  postroute_hold = Step( 'cadence-innovus-postroute_hold',default=True )
  signoff        = Step( 'cadence-innovus-signoff',       default=True )
  pt_signoff     = Step( 'synopsys-pt-timing-signoff',    default=True )
  genlibdb       = Step( 'synopsys-ptpx-genlibdb',        default=True )
  debugcalibre   = Step( 'cadence-innovus-debug-calibre', default=True )

  # Add custom timing scripts
  custom_timing_steps = [ synth, postcts_hold, signoff ] # connects to these
  for c_step in custom_timing_steps:
    c_step.extend_inputs( custom_timing_assert.all_outputs() )

  # Add extra input edges to innovus steps that need custom tweaks
  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )
  genlibdb.extend_inputs( genlibdb_constraints.all_outputs() )
  synth.extend_inputs( custom_genus_scripts.all_outputs() )
  iflow.extend_inputs( custom_flowgen_setup.all_outputs() )

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

  # Add graph inputs and outputs so this can be used in hierarchical flows

  # Inputs
  g.add_input( 'design.v', rtl.i('design.v') )

  # Outputs
  g.add_output( 'Tile_PE_tt.lib',      genlibdb.o('design.lib')       )
  g.add_output( 'Tile_PE_tt.db',       genlibdb.o('design.db')        )
  g.add_output( 'Tile_PE.lef',         signoff.o('design.lef')        )
  g.add_output( 'Tile_PE.gds',         signoff.o('design-merged.gds') )
  g.add_output( 'Tile_PE.sdf',         signoff.o('design.sdf')        )
  g.add_output( 'Tile_PE.vcs.v',       signoff.o('design.vcs.v')      )
  g.add_output( 'Tile_PE.vcs.pg.v',    signoff.o('design.vcs.pg.v')   )
  g.add_output( 'Tile_PE.spef.gz',     signoff.o('design.spef.gz')    )
  g.add_output( 'Tile_PE.pt.sdc',      signoff.o('design.pt.sdc')     )
  g.add_output( 'Tile_PE.lvs.v',       lvs.o('design_merged.lvs.v')   )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info                     )
  g.add_step( rtl                      )
  g.add_step( constraints              )
  g.add_step( custom_dc_scripts        )
  g.add_step( synth                    )
  g.add_step( custom_timing_assert     )
  g.add_step( custom_genus_scripts     )
  g.add_step( iflow                    )
  g.add_step( custom_flowgen_setup     )
  g.add_step( init                     )
  g.add_step( custom_init              )
  g.add_step( power                    )
  g.add_step( custom_power             )
  g.add_step( place                    )
  g.add_step( cts                      )
  g.add_step( postcts_hold             )
  g.add_step( route                    )
  g.add_step( postroute                )
  g.add_step( postroute_hold           )
  g.add_step( signoff                  )
  g.add_step( pt_signoff               )
  g.add_step( genlibdb_constraints     )
  g.add_step( genlibdb                 )
  g.add_step( lib2db                   )
  g.add_step( drc                      )
  g.add_step( lvs                      )
  g.add_step( debugcalibre             )
  g.add_step( application              )
  g.add_step( testbench                )
  g.add_step( post_pnr_power           )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Dynamically add edges

  # Connect by name

  g.connect_by_name( adk,                       synth            )
  g.connect_by_name( adk,                       iflow            )
  g.connect_by_name( adk,                       init             )
  g.connect_by_name( adk,                       power            )
  g.connect_by_name( adk,                       place            )
  g.connect_by_name( adk,                       cts              )
  g.connect_by_name( adk,                       postcts_hold     )
  g.connect_by_name( adk,                       route            )
  g.connect_by_name( adk,                       postroute        )
  g.connect_by_name( adk,                       postroute_hold   )
  g.connect_by_name( adk,                       signoff          )
  g.connect_by_name( adk,                       drc              )
  g.connect_by_name( adk,                       lvs              )

  g.connect_by_name( rtl,                       synth            )
  g.connect_by_name( constraints,               synth            )
  g.connect_by_name( custom_genus_scripts,      synth            )
  g.connect_by_name( constraints,               iflow            )
  g.connect_by_name( custom_dc_scripts,         iflow            )

  for c_step in custom_timing_steps:
    g.connect_by_name( custom_timing_assert, c_step )

  g.connect_by_name( synth,                 iflow                )
  g.connect_by_name( synth,                 init                 )
  g.connect_by_name( synth,                 power                )
  g.connect_by_name( synth,                 place                )
  g.connect_by_name( synth,                 cts                  )
  g.connect_by_name( synth,                 custom_flowgen_setup )

  g.connect_by_name( custom_flowgen_setup,  iflow                )
  g.connect_by_name( iflow,                 init                 )
  g.connect_by_name( iflow,                 power                )
  g.connect_by_name( iflow,                 place                )
  g.connect_by_name( iflow,                 cts                  )
  g.connect_by_name( iflow,                 postcts_hold         )
  g.connect_by_name( iflow,                 route                )
  g.connect_by_name( iflow,                 postroute            )
  g.connect_by_name( iflow,                 postroute_hold       )
  g.connect_by_name( iflow,                 signoff              )

  g.connect_by_name( custom_init,           init                 )
  g.connect_by_name( custom_power,          power                )

  g.connect_by_name( init,                  power                )
  g.connect_by_name( power,                 place                )
  g.connect_by_name( place,                 cts                  )
  g.connect_by_name( cts,                   postcts_hold         )
  g.connect_by_name( postcts_hold,          route                )
  g.connect_by_name( route,                 postroute            )
  g.connect_by_name( postroute,             postroute_hold       )
  g.connect_by_name( postroute_hold,        signoff              )

  g.connect_by_name( signoff,               drc                  )
  g.connect_by_name( signoff,               lvs                  )

  g.connect_by_name( signoff,               genlibdb             )
  g.connect_by_name( adk,                   genlibdb             )
  g.connect_by_name( genlibdb_constraints,  genlibdb             )
  
  g.connect_by_name( genlibdb,              lib2db               )

  g.connect_by_name( adk,                   pt_signoff           )
  g.connect_by_name( signoff,               pt_signoff           )

  g.connect_by_name( application,           testbench            )
  g.connect_by_name( application,           post_pnr_power       )
  g.connect_by_name( signoff,               post_pnr_power       )
  g.connect_by_name( pt_signoff,            post_pnr_power       )
  g.connect_by_name( testbench,             post_pnr_power       )

  g.connect_by_name( adk,                   debugcalibre         )
  g.connect_by_name( synth,                 debugcalibre         )
  g.connect_by_name( iflow,                 debugcalibre         )
  g.connect_by_name( signoff,               debugcalibre         )

  # New 'custom_cts' step added for gf12
  cts.extend_inputs( custom_cts.all_outputs() )
  g.add_step(        custom_cts               )
  g.connect_by_name( custom_cts,   cts        )

  # Need this because gf12/intel16 uses innovus for lib generation
  g.connect_by_name( iflow,    genlibdb       )

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

  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

  init.update_params( { 'core_density_target': parameters['core_density_target'] }, True )
  init.update_params( { 'order': [
    'pre-init.tcl',
    'main.tcl',
    'innovus-pnr-config.tcl',
    'dont-use.tcl',
    'quality-of-life.tcl',
    'floorplan.tcl',
    'pin-assignments.tcl',
    'create-rows.tcl',
    'add-tracks.tcl',
    'create-boundary-blockage.tcl',
    'add-endcaps-welltaps.tcl',
    'insert-input-antenna-diodes.tcl',
    'create-special-grid.tcl',
    'make-path-groups.tcl',
    'additional-path-groups.tcl',
    'reporting.tcl'
  ] } )

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
  # g.plot()
