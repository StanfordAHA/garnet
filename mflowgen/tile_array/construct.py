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

  adk_name = get_sys_adk()
  adk_view = 'multivt'

  parameters = {
    'construct_path'    : __file__,
    'design_name'       : 'Interconnect',
    'clock_period'      : 1.1,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    # Synthesis
    'flatten_effort'    : 3,
    'topographical'     : True,
    # RTL Generation
    'array_width'       : 32,
    'array_height'      : 16,
    'interconnect_only' : False,
    # Power Domains
    'PWR_AWARE'         : True,
    # Useful Skew (CTS)
    'useful_skew'       : False,
    # hold target slack
    'hold_target_slack' : 0.015,
    # Pipeline stage insertion
    'pipeline_config_interval': 8,
    'pipeline_stage_height': 30,
    # Testing
    'testbench_name'    : 'Interconnect_tb',
    # I am defaulting to True because nothing is worse than finishing
    # a sim and needing the wave but not having it...
    'waves'             : True,
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
  Tile_MemCore   = Step( this_dir + '/Tile_MemCore'                        )
  Tile_PE        = Step( this_dir + '/Tile_PE'                             )
  constraints    = Step( this_dir + '/constraints'                         )
  dc_postcompile = Step( this_dir + '/custom-dc-postcompile'               )
  custom_init    = Step( this_dir + '/custom-init'                         )
  custom_power   = Step( this_dir + '/../common/custom-power-hierarchical' )
  custom_cts     = Step( this_dir + '/custom-cts-overrides'                )
  custom_lvs     = Step( this_dir + '/custom-lvs-rules'                    )
  gls_args       = Step( this_dir + '/gls_args'                            )
  testbench      = Step( this_dir + '/testbench'                           )
  lib2db         = Step( this_dir + '/../common/synopsys-dc-lib2db'        )


  # Default steps

  info           = Step( 'info',                           default=True )
  #constraints    = Step( 'constraints',                    default=True )
  #dc             = Step( 'synopsys-dc-synthesis',          default=True )
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
  #genlibdb       = Step( 'synopsys-ptpx-genlibdb',         default=True )
  genlib         = Step( 'cadence-genus-genlib',           default=True )
  if which("calibre") is not None:
      drc            = Step( 'mentor-calibre-drc',             default=True )
      lvs            = Step( 'mentor-calibre-lvs',             default=True )
  else:
      drc            = Step( 'cadence-pegasus-drc',            default=True )
      lvs            = Step( 'cadence-pegasus-lvs',            default=True )
  debugcalibre   = Step( 'cadence-innovus-debug-calibre',   default=True )
  vcs_sim        = Step( 'synopsys-vcs-sim',                default=True )

  # Add cgra tile macro inputs to downstream nodes

  #dc.extend_inputs( ['Tile_PE.db'] )
  synth.extend_inputs( ['Tile_PE_tt.lib'] )
  #dc.extend_inputs( ['Tile_MemCore.db'] )
  synth.extend_inputs( ['Tile_MemCore_tt.lib'] )
  pt_signoff.extend_inputs( ['Tile_PE_tt.db'] )
  pt_signoff.extend_inputs( ['Tile_MemCore_tt.db'] )
  #genlibdb.extend_inputs( ['Tile_PE.db'] )
  genlib.extend_inputs( ['Tile_PE_tt.lib'] )
  #genlibdb.extend_inputs( ['Tile_MemCore.db'] )
  genlib.extend_inputs( ['Tile_MemCore_tt.lib'] )

  e2e_apps = ["tests/conv_3_3", "apps/cascade", "apps/harris_auto", "apps/resnet_i1_o1_mem", "apps/resnet_i1_o1_pond"]

  # Only use these steps with power domains off and no flattening...
  use_e2e = True
  e2e_tb_nodes = {}
  e2e_sim_nodes = {}
  e2e_power_nodes = {}
  if use_e2e:
    for app in e2e_apps:
        e2e_testbench = Step( this_dir + '/e2e_testbench' )
        e2e_xcelium_sim = Step( this_dir + '/../common/cadence-xcelium-sim' )
        e2e_ptpx_gl     = Step( this_dir + '/../common/synopsys-ptpx-gl'    ) 
        # Simple rename
        app_name = app.split("/")[1]
        e2e_testbench.set_name(f"e2e_testbench_{app_name}") 
        e2e_xcelium_sim.set_name(f"e2e_xcelium_sim_{app_name}")
        e2e_ptpx_gl.set_name(f"e2e_ptpx_gl_{app_name}")
        e2e_tb_nodes[app] = e2e_testbench
        e2e_sim_nodes[app] = e2e_xcelium_sim
        e2e_power_nodes[app] = e2e_ptpx_gl

        # override app_to_run param of the testbench gen
        e2e_testbench.set_param("app_to_run", app)

        # Send all the relevant post-pnr files to sim 
        e2e_xcelium_sim.extend_inputs(Tile_MemCore.all_outputs())
        e2e_xcelium_sim.extend_inputs(Tile_PE.all_outputs())
        e2e_xcelium_sim.extend_inputs(['design.vcs.pg.v'])
        e2e_xcelium_sim.extend_inputs(['input.raw'])

        # Configure the ptpx step a little differently...
        e2e_ptpx_gl.set_param("strip_path", "Interconnect_tb/dut")
        e2e_ptpx_gl.extend_inputs(e2e_testbench.all_outputs())
        e2e_ptpx_gl.extend_inputs(Tile_MemCore.all_outputs())
        e2e_ptpx_gl.extend_inputs(Tile_PE.all_outputs())

  # These steps need timing info for cgra tiles
  tile_steps = \
    [ iflow, init, power, place, cts, postcts_hold,
      route, postroute, signoff ]

  for step in tile_steps:
    step.extend_inputs( ['Tile_PE_tt.lib', 'Tile_PE.lef'] )
    step.extend_inputs( ['Tile_MemCore_tt.lib', 'Tile_MemCore.lef'] )

  # Need the netlist and SDF files for gate-level sim

  vcs_sim.extend_inputs( ['Tile_PE.vcs.v', 'Tile_PE.sdf'] )
  vcs_sim.extend_inputs( ['Tile_MemCore.vcs.v', 'Tile_MemCore.sdf'] )

  # Need the cgra tile gds's to merge into the final layout

  signoff.extend_inputs( ['Tile_PE.gds'] )
  signoff.extend_inputs( ['Tile_MemCore.gds'] )

  # Need LVS verilog files for both tile types to do LVS

  lvs.extend_inputs( ['Tile_PE.lvs.v'] )
  lvs.extend_inputs( ['Tile_MemCore.lvs.v'] )
  
  # Need sram spice file for LVS

  lvs.extend_inputs( ['sram.spi'] )

  # Extra dc inputs
  #dc.extend_inputs( dc_postcompile.all_outputs() )
  #synth.extend_inputs( dc_postcompile.all_outputs() )

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  cts.extend_inputs( custom_cts.all_outputs() )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info           )
  g.add_step( rtl            )
  g.add_step( Tile_MemCore   )
  g.add_step( Tile_PE        )
  g.add_step( constraints    )
  g.add_step( dc_postcompile )
  g.add_step( synth          )
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
  g.add_step( genlib         )
  g.add_step( lib2db         )
  g.add_step( drc            )
  g.add_step( custom_lvs     )
  g.add_step( lvs            )
  g.add_step( debugcalibre   )
  g.add_step( gls_args       )
  g.add_step( testbench      )
  g.add_step( vcs_sim        )

  if use_e2e:
    for app in e2e_apps:
        g.add_step( e2e_tb_nodes[app]    )
        g.add_step( e2e_sim_nodes[app]   )
        g.add_step( e2e_power_nodes[app] )
  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( adk,      synth           )
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

  if use_e2e:
    for app in e2e_apps:
        g.connect_by_name( adk,               e2e_sim_nodes[app] )
        g.connect_by_name( Tile_MemCore,      e2e_sim_nodes[app] )
        g.connect_by_name( Tile_PE,           e2e_sim_nodes[app] )
        g.connect_by_name( e2e_tb_nodes[app], e2e_sim_nodes[app] )
        g.connect_by_name( signoff,           e2e_sim_nodes[app] )

        g.connect_by_name( adk,                e2e_power_nodes[app] )
        g.connect_by_name( Tile_MemCore,       e2e_power_nodes[app] )
        g.connect_by_name( Tile_PE,            e2e_power_nodes[app] )
        g.connect_by_name( signoff,            e2e_power_nodes[app] )
        g.connect_by_name( e2e_tb_nodes[app],  e2e_power_nodes[app] )
        g.connect_by_name( e2e_sim_nodes[app], e2e_power_nodes[app] )
  # In our CGRA, the tile pattern is:
  # PE PE PE Mem PE PE PE Mem ...
  # Thus, if there are < 4 columns, the the array won't contain any
  # memory tiles. If this is the case, we don't need to run the
  # memory tile flow.
  if parameters['array_width'] > 3:
      # inputs to Tile_MemCore
      g.connect_by_name( rtl, Tile_MemCore )
      # outputs from Tile_MemCore
      #g.connect_by_name( Tile_MemCore,      dc             )
      g.connect_by_name( Tile_MemCore,      synth          )
      g.connect_by_name( Tile_MemCore,      iflow          )
      g.connect_by_name( Tile_MemCore,      init           )
      g.connect_by_name( Tile_MemCore,      power          )
      g.connect_by_name( Tile_MemCore,      place          )
      g.connect_by_name( Tile_MemCore,      cts            )
      g.connect_by_name( Tile_MemCore,      postcts_hold   )
      g.connect_by_name( Tile_MemCore,      route          )
      g.connect_by_name( Tile_MemCore,      postroute      )
      g.connect_by_name( Tile_MemCore,      postroute_hold )
      g.connect_by_name( Tile_MemCore,      signoff        )
      g.connect_by_name( Tile_MemCore,      pt_signoff     )
      #g.connect_by_name( Tile_MemCore,      genlibdb       )
      g.connect_by_name( Tile_MemCore,      genlib         )
      g.connect_by_name( Tile_MemCore,      drc            )
      g.connect_by_name( Tile_MemCore,      lvs            )
      # These rules LVS BOX the SRAM macro, so they should
      # only be used if memory tile is present
      g.connect_by_name( custom_lvs,        lvs            )
      g.connect_by_name( Tile_MemCore,      vcs_sim        )

  
  # inputs to Tile_PE
  g.connect_by_name( rtl, Tile_PE )
  # outputs from Tile_PE
  #g.connect_by_name( Tile_PE,      dc             )
  g.connect_by_name( Tile_PE,      synth          )
  g.connect_by_name( Tile_PE,      iflow          )
  g.connect_by_name( Tile_PE,      init           )
  g.connect_by_name( Tile_PE,      power          )
  g.connect_by_name( Tile_PE,      place          )
  g.connect_by_name( Tile_PE,      cts            )
  g.connect_by_name( Tile_PE,      postcts_hold   )
  g.connect_by_name( Tile_PE,      route          )
  g.connect_by_name( Tile_PE,      postroute      )
  g.connect_by_name( Tile_PE,      postroute_hold )
  g.connect_by_name( Tile_PE,      signoff        )
  g.connect_by_name( Tile_PE,      pt_signoff     )
  #g.connect_by_name( Tile_PE,      genlibdb       )
  g.connect_by_name( Tile_PE,      genlib         )
  g.connect_by_name( Tile_PE,      drc            )
  g.connect_by_name( Tile_PE,      lvs            )

  #g.connect_by_name( rtl,            dc        )
  #g.connect_by_name( constraints,    dc        )
  #g.connect_by_name( dc_postcompile, dc        )

  #g.connect_by_name( dc,       iflow        )
  #g.connect_by_name( dc,       init         )
  #g.connect_by_name( dc,       power        )
  #g.connect_by_name( dc,       place        )
  #g.connect_by_name( dc,       cts          )


  g.connect_by_name( rtl,            synth        )
  g.connect_by_name( rtl,            synth        )
  g.connect_by_name( constraints,    synth        )
  #g.connect_by_name( dc_postcompile, synth        )

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
  g.connect(signoff.o('design-merged.gds'), drc.i('design_merged.gds'))
  g.connect(signoff.o('design-merged.gds'), lvs.i('design_merged.gds'))

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )
  
  #g.connect_by_name( adk,          genlibdb   )
  g.connect_by_name( adk,          genlib   )
  #g.connect_by_name( signoff,      genlibdb   )
  g.connect_by_name( signoff,      genlib   )
  
  g.connect_by_name( genlib,       lib2db   )

  g.connect_by_name( adk,      debugcalibre )
  #g.connect_by_name( dc,       debugcalibre )
  g.connect_by_name( synth,    debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( drc,      debugcalibre )
  g.connect_by_name( lvs,      debugcalibre )

  g.connect_by_name( adk,           vcs_sim )
  g.connect_by_name( testbench,     vcs_sim )
  g.connect_by_name( gls_args,      vcs_sim )
  g.connect_by_name( signoff,       vcs_sim )
  g.connect_by_name( Tile_PE,       vcs_sim )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  # Init needs pipeline params for floorplanning
  init.update_params({ 'pipeline_config_interval': parameters['pipeline_config_interval'] }, True)
  init.update_params({ 'pipeline_stage_height': parameters['pipeline_stage_height'] }, True)
  
  # CTS uses height/width param to do CTS endpoint overrides properly
  cts.update_params({ 'array_width':  parameters['array_width']}, True)
  cts.update_params({ 'array_height':  parameters['array_height']}, True)

  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

  #order = synth.get_param('order')
  #compile_idx = order.index( 'compile.tcl' )
  #order.insert ( compile_idx + 1, 'custom-dc-postcompile.tcl' )
  #dc.update_params( { 'order': order } )
  #synth.update_params( { 'order': order } )

  # genlibdb -- Remove 'report-interface-timing.tcl' beacuse it takes
  # very long and is not necessary
  #order = genlibdb.get_param('order')
  #order.remove( 'write-interface-timing.tcl' )
  #genlibdb.update_params( { 'order': order } )

  # init -- Add 'dont-touch.tcl' before reporting

  order = init.get_param('order') # get the default script run order
  reporting_idx = order.index( 'reporting.tcl' ) # find reporting.tcl
  # Add dont-touch before reporting
  order.insert ( reporting_idx, 'dont-touch.tcl' )
  init.update_params( { 'order': order } )
  
  # We are overriding certain pin types for CTS, so we need to
  # add the script that does that to the CTS order
  order = cts.get_param('order')
  main_idx = order.index( 'main.tcl' )
  order.insert( main_idx, 'cts-overrides.tcl' )
  cts.update_params( { 'order': order } )

                                                                                                   
  # Remove 
  #dc_postconditions = dc.get_postconditions()
  #for postcon in dc_postconditions:
  #    if 'percent_clock_gated' in postcon:
  #        dc_postconditions.remove(postcon)
  #dc.set_postconditions( dc_postconditions )

  synth_postconditions = synth.get_postconditions()
  for postcon in synth_postconditions:
      if 'percent_clock_gated' in postcon:
          synth_postconditions.remove(postcon)
  synth.set_postconditions( synth_postconditions )



  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


