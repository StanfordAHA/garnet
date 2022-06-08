#! /usr/bin/env python
#=========================================================================
# construct.py
#=========================================================================
# Author :
# Date   :
#

import os
import sys
import pathlib

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
    'construct_path' : __file__,
    'design_name'    : 'global_buffer',
    'clock_period'      : 1.11,
    'sim_clock_period'  : 1.42,
    'adk'            : adk_name,
    'adk_view'       : adk_view,
    # Synthesis
    'flatten_effort' : 3,
    'topographical'  : True,
    # hold target slack
    'hold_target_slack'   : 0.03,
    # array_width = width of CGRA below GLB; `pin-assignments.tcl` uses
    # these parms to set up per-cgra-column ports connecting glb tile
    # signals in glb_top to corresponding CGRA tile columns below glb_top
    'array_width'         : 32,
    'num_glb_tiles'       : 16,
    'tool'                : "VCS",
    # glb tile memory size (unit: KB)
    'use_container' : False,
    'glb_tile_mem_size' : 256,
    'rtl_testvectors' : ["test01", "test02", "test03", "test04", "test05", "test06", "test07", "test08", "test09", "test10", "test11"],
    'gls_testvectors' : ["test01", "test02", "test03", "test04", "test05", "test06", "test07", "test08", "test09", "test10", "test11"],
    'sdf' : True,
    'saif' : False,
    'waveform' : True,
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl               = Step( this_dir + '/../common/rtl'                       )
  testbench         = Step( this_dir + '/testbench'                           )
  sim_compile       = Step( this_dir + '/sim-compile'                         )
  sim_run           = Step( this_dir + '/sim-run'                             )
  sim_gl_compile    = Step( this_dir + '/sim-gl-compile'                      )
  glb_tile          = Step( this_dir + '/glb_tile'                            )
  constraints       = Step( this_dir + '/constraints'                         )
  custom_init       = Step( this_dir + '/custom-init'                         )
  custom_lvs        = Step( this_dir + '/custom-lvs-rules'                    )
  custom_power      = Step( this_dir + '/../common/custom-power-hierarchical' )
  genlib            = Step( this_dir + '/../common/cadence-innovus-genlib'    )
  lib2db            = Step( this_dir + '/../common/synopsys-dc-lib2db'        )

  # Default steps

  info           = Step( 'info',                            default=True )
  synth          = Step( 'cadence-genus-synthesis',         default=True )
  iflow          = Step( 'cadence-innovus-flowsetup',       default=True )
  init           = Step( 'cadence-innovus-init',            default=True )
  power          = Step( 'cadence-innovus-power',           default=True )
  place          = Step( 'cadence-innovus-place',           default=True )
  cts            = Step( 'cadence-innovus-cts',             default=True )
  postcts_hold   = Step( 'cadence-innovus-postcts_hold',    default=True )
  route          = Step( 'cadence-innovus-route',           default=True )
  postroute      = Step( 'cadence-innovus-postroute',       default=True )
  postroute_hold = Step( 'cadence-innovus-postroute_hold',  default=True )
  signoff        = Step( 'cadence-innovus-signoff',         default=True )
  pt_signoff     = Step( 'synopsys-pt-timing-signoff',      default=True )
  if which("calibre") is not None:
      drc            = Step( 'mentor-calibre-drc',            default=True )
      lvs            = Step( 'mentor-calibre-lvs',            default=True )
  else:
      drc            = Step( 'cadence-pegasus-drc',           default=True )
      lvs            = Step( 'cadence-pegasus-lvs',           default=True )
  debugcalibre   = Step( 'cadence-innovus-debug-calibre',   default=True )

  if parameters['tool'] == 'VCS':
    sim_compile.extend_outputs(['simv', 'simv.daidir'])
    sim_gl_compile.extend_outputs(['simv', 'simv.daidir'])
    sim_run.extend_inputs(['simv', 'simv.daidir'])
  elif parameters['tool'] == 'XCELIUM':
    sim_compile.extend_outputs(['xcelium.d'])
    sim_gl_compile.extend_outputs(['xcelium.d'])
    sim_run.extend_inputs(['xcelium.d'])

  sim_gl_run_nodes = {}
  ptpx_gl_nodes = {}
  for test in parameters["gls_testvectors"]:
    sim_gl_run        = Step( this_dir + '/sim-gl-run'       )
    ptpx_gl           = Step( this_dir + '/synopsys-ptpx-gl' )

    # rename
    sim_gl_run.set_name(f"sim_gl_run_{test}")
    ptpx_gl.set_name(f"ptpx_gl_{test}")
    sim_gl_run_nodes[test] = sim_gl_run
    ptpx_gl_nodes[test] = ptpx_gl
    sim_gl_run.update_params( {'test' : test}, allow_new=True)
    # Gate-level ptpx node
    ptpx_gl.set_param("strip_path", "top/dut")
    ptpx_gl.extend_inputs(glb_tile.all_outputs())
    if parameters['tool'] == 'VCS':
      sim_gl_run.extend_inputs(['simv', 'simv.daidir'])
    elif parameters['tool'] == 'XCELIUM':
      sim_gl_run.extend_inputs(['xcelium.d'])
    if parameters['saif'] == True:
      sim_gl_run.extend_postconditions( ["assert File( 'outputs/run.saif' ) "] )
    if parameters['waveform'] == True:
      sim_gl_run.extend_postconditions( ["assert File( 'outputs/run.fsdb' ) "] )


  # Add header files to outputs
  rtl.extend_outputs( ['header'] )
  rtl.extend_postconditions( ["assert File( 'outputs/header' ) "] )

  # Add (dummy) parameters to the default innovus init step

  init.update_params( {
    'core_width'  : 0,
    'core_height' : 0
    }, allow_new=True )

  # Add glb_tile macro inputs to downstream nodes

  pt_signoff.extend_inputs( ['glb_tile_tt.db'] )

  # These steps need timing info for glb_tiles
  tile_steps = \
    [ synth, iflow, init, power, place, cts, postcts_hold,
      route, postroute, postroute_hold, signoff, genlib ]

  for step in tile_steps:
    step.extend_inputs( ['glb_tile_tt.lib', 'glb_tile.lef'] )

  # Need the glb_tile gds to merge into the final layout

  signoff.extend_inputs( ['glb_tile.gds'] )

  # Need glb_tile lvs.v file for LVS

  lvs.extend_inputs( ['glb_tile.lvs.v'] )

  # Need sram spice file for LVS
  lvs.extend_inputs( ['glb_tile_sram.spi'] )

  # Need glb_tile for genlib
  genlib.extend_inputs( ['glb_tile_tt.lib'] )

  xlist = synth.get_postconditions()
  xlist = \
    [ _ for _ in xlist if 'percent_clock_gated' not in _ ]
  xlist = synth.set_postconditions( xlist )

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )


  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info           )
  g.add_step( rtl            )
  g.add_step( testbench      )
  g.add_step( sim_compile    )
  g.add_step( sim_run        )
  g.add_step( sim_gl_compile )
  g.add_step( glb_tile       )
  g.add_step( constraints    )
  g.add_step( synth          )
  g.add_step( iflow          )
  g.add_step( init           )
  g.add_step( custom_init    )
  g.add_step( power          )
  g.add_step( custom_power   )
  g.add_step( place          )
  g.add_step( cts            )
  g.add_step( postcts_hold   )
  g.add_step( route          )
  g.add_step( postroute      )
  g.add_step( postroute_hold )
  g.add_step( signoff        )
  g.add_step( pt_signoff     )
  g.add_step( genlib         )
  g.add_step( lib2db         )
  g.add_step( drc            )
  g.add_step( lvs            )
  g.add_step( custom_lvs     )
  g.add_step( debugcalibre   )

  for test in parameters["gls_testvectors"]:
    g.add_step(sim_gl_run_nodes[test])
    g.add_step(ptpx_gl_nodes[test])

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
  g.connect_by_name( adk,      genlib         )

  g.connect_by_name( glb_tile,      synth        )
  g.connect_by_name( glb_tile,      iflow        )
  g.connect_by_name( glb_tile,      init         )
  g.connect_by_name( glb_tile,      power        )
  g.connect_by_name( glb_tile,      place        )
  g.connect_by_name( glb_tile,      cts          )
  g.connect_by_name( glb_tile,      postcts_hold )
  g.connect_by_name( glb_tile,      route        )
  g.connect_by_name( glb_tile,      postroute    )
  g.connect_by_name( glb_tile,      postroute_hold )
  g.connect_by_name( glb_tile,      signoff      )
  g.connect_by_name( glb_tile,      pt_signoff   )
  g.connect_by_name( glb_tile,      genlib       )
  g.connect_by_name( glb_tile,      drc          )
  g.connect_by_name( glb_tile,      lvs          )

  g.connect_by_name( rtl,         sim_compile  )
  g.connect_by_name( testbench,   sim_compile  )
  g.connect_by_name( testbench,   sim_run      )
  g.connect_by_name( sim_compile, sim_run      )

  g.connect_by_name( rtl,         synth        )
  g.connect_by_name( constraints, synth        )

  # glb_tile can use the same rtl as glb_top
  g.connect_by_name( rtl,         glb_tile     )

  g.connect_by_name( synth,       iflow        )
  g.connect_by_name( synth,       init         )
  g.connect_by_name( synth,       power        )
  g.connect_by_name( synth,       place        )
  g.connect_by_name( synth,       cts          )

  g.connect_by_name( iflow,    init         )
  g.connect_by_name( iflow,    power        )
  g.connect_by_name( iflow,    place        )
  g.connect_by_name( iflow,    cts          )
  g.connect_by_name( iflow,    postcts_hold )
  g.connect_by_name( iflow,    route        )
  g.connect_by_name( iflow,    postroute    )
  g.connect_by_name( iflow,    postroute_hold )
  g.connect_by_name( iflow,    signoff      )
  g.connect_by_name( iflow,    genlib       )

  g.connect_by_name( custom_init,  init     )
  g.connect_by_name( custom_power, power    )
  g.connect_by_name( custom_lvs,   lvs      )

  g.connect_by_name( init,         power          )
  g.connect_by_name( power,        place          )
  g.connect_by_name( place,        cts            )
  g.connect_by_name( cts,          postcts_hold   )
  g.connect_by_name( postcts_hold, route          )
  g.connect_by_name( route,        postroute      )
  g.connect_by_name( postroute,    postroute_hold )
  g.connect_by_name( postroute_hold,    signoff   )
  g.connect_by_name( signoff,      drc            )
  g.connect_by_name( signoff,      lvs            )
  g.connect(signoff.o('design-merged.gds'), drc.i('design_merged.gds'))
  g.connect(signoff.o('design-merged.gds'), lvs.i('design_merged.gds'))

  g.connect_by_name( adk,          pt_signoff     )
  g.connect_by_name( signoff,      pt_signoff     )

  g.connect_by_name( adk,          genlib     )
  g.connect_by_name( signoff,      genlib     )

  g.connect_by_name( rtl,        sim_gl_compile )
  g.connect_by_name( testbench,  sim_gl_compile )
  g.connect_by_name( adk,        sim_gl_compile )
  g.connect_by_name( glb_tile,   sim_gl_compile )
  g.connect_by_name( signoff,    sim_gl_compile )

  for test in parameters["gls_testvectors"]:
    g.connect_by_name( testbench, sim_gl_run_nodes[test] )
    g.connect_by_name( sim_gl_compile, sim_gl_run_nodes[test] )

  for test in parameters["gls_testvectors"]:
    g.connect_by_name( adk,                    ptpx_gl_nodes[test] )
    g.connect_by_name( glb_tile,               ptpx_gl_nodes[test] )
    g.connect_by_name( signoff,                ptpx_gl_nodes[test] )
    g.connect_by_name( sim_gl_run_nodes[test], ptpx_gl_nodes[test] )

  g.connect_by_name( genlib,       lib2db   )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( synth,    debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( drc,      debugcalibre )
  g.connect_by_name( lvs,      debugcalibre )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

  # rtl parameters update
  rtl.update_params( { 'glb_only': True }, allow_new=True )

  # pin assignment parameters update
  init.update_params( { 'array_width': parameters['array_width'] }, allow_new=True )
  init.update_params( { 'num_glb_tiles': parameters['num_glb_tiles'] }, allow_new=True )

  # Change nthreads
  synth.update_params( { 'nthreads': 4 } )
  iflow.update_params( { 'nthreads': 4 } )

  order = init.get_param('order') # get the default script run order
  reporting_idx = order.index( 'reporting.tcl' ) # find reporting.tcl
  # Add dont-touch before reporting
  order.insert ( reporting_idx, 'dont-touch.tcl' )
  init.update_params( { 'order': order } )

  # Increase hold slack on postroute_hold step
  postroute_hold.update_params( { 'hold_target_slack': parameters['hold_target_slack'] }, allow_new=True  )

  # useful_skew
  cts.update_params( { 'useful_skew': False }, allow_new=True )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


