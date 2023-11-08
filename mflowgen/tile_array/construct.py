#! /usr/bin/env python
#=========================================================================
# construct.py
#=========================================================================
# Author : 
# Date   : 
#

import os
import sys

from mflowgen.components import Graph, Step, Subgraph
from shutil import which
from common.get_sys_adk import get_sys_adk

def construct():

  g = Graph()

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  adk_name = get_sys_adk()
  adk_view = 'multivt'
  read_hdl_defines = 'INTEL16'
  which_soc = 'opal'

  parameters = {
    'construct_path'    : __file__,
    'design_name'       : 'Interconnect',
    'clock_period'      : 1.5 * 1000,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    'adk_stdcell'       : 'b15_7t_108pp',
    'adk_libmodel'      : 'nldm',
    # Synthesis
    'flatten_effort'    : 3,
    'topographical'     : True,
    'read_hdl_defines'  : read_hdl_defines,
    # RTL Generation
    'array_width'       : 28,
    'array_height'      : 16,
    'interconnect_only' : False,
    # Power Domains
    'PWR_AWARE'         : True,
    # Useful Skew (CTS)
    'useful_skew'       : False,
    # hold target slack
    'hold_target_slack' : 0.07,
    # Pipeline stage insertion
    'pipeline_config_interval': 8,
    'pipeline_stage_height': 30,
    # Testing
    'testbench_name'    : 'Interconnect_tb',
    # I am defaulting to True because nothing is worse than finishing
    # a sim and needing the wave but not having it...
    'waves'             : True,
    'drc_env_setup'     : 'drcenv-block.sh'
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # Initialization orders
  init_order = [
    'pre-init.tcl',
    'main.tcl',
    'innovus-pnr-config.tcl',
    'dont-use.tcl',
    'quality-of-life.tcl',
    'floorplan.tcl',
    'create-rows.tcl',
    'add-endcaps-welltaps.tcl',
    'pin-assignments.tcl',
    'add-tracks.tcl',
    # 'create-boundary-blockage.tcl',
    # 'insert-input-antenna-diodes.tcl',
    'create-special-grid.tcl',
    'make-path-groups.tcl',
    'dont-touch.tcl',
    'reporting.tcl'
  ]

  # ADK step
  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Subgraphs
  Tile_MemCore   = Subgraph( this_dir + '/../Tile_MemCore', 'Tile_MemCore'    )
  Tile_PE        = Subgraph( this_dir + '/../Tile_PE',      'Tile_PE'         )

  # Custom steps
  rtl            = Step( this_dir + '/../common/rtl'                          )
  constraints    = Step( this_dir + '/constraints'                            )
  custom_init    = Step( this_dir + '/custom-init'                            )
  custom_power   = Step( this_dir + '/../common/custom-power-hierarchical'    )
  custom_cts     = Step( this_dir + '/custom-cts-overrides'                   )
  gls_args       = Step( this_dir + '/gls_args'                               )
  testbench      = Step( this_dir + '/testbench'                              )
  custom_hack_sdc_unit = Step( this_dir + '/../common/custom-hack-sdc-unit'   )

  # Default steps
  info           = Step( 'info',                           default=True )
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
  genlibdb_tt    = Step( 'synopsys-ptpx-genlibdb',         default=True )
  genlibdb_ff    = Step( 'synopsys-ptpx-genlibdb',         default=True )
  debugcalibre   = Step( 'cadence-innovus-debug-calibre',  default=True )
  vcs_sim        = Step( 'synopsys-vcs-sim',               default=True )
  drc            = Step( this_dir + '/../common/intel16-synopsys-icv-drc' )
  lvs            = Step( this_dir + '/../common/intel16-synopsys-icv-lvs' )

  genlibdb_tt.set_name( 'synopsys-ptpx-genlibdb-tt' )
  genlibdb_ff.set_name( 'synopsys-ptpx-genlibdb-ff' )

  # Add cgra tile macro inputs to downstream nodes
  synth.extend_inputs( ['Tile_PE-typical.lib', 'Tile_PE.lef'] )
  synth.extend_inputs( ['Tile_MemCore-typical.lib', 'Tile_MemCore.lef'] )
  pt_signoff.extend_inputs( ['Tile_PE-typical.db'] )
  pt_signoff.extend_inputs( ['Tile_MemCore-typical.db'] )
  pt_signoff.extend_inputs( ['Tile_PE-bc.db'] )
  pt_signoff.extend_inputs( ['Tile_MemCore-bc.db'] )
  genlibdb_tt.extend_inputs( ['Tile_PE-typical.db'] )
  genlibdb_tt.extend_inputs( ['Tile_MemCore-typical.db'] )
  genlibdb_ff.extend_inputs( ['Tile_PE-bc.db'] )
  genlibdb_ff.extend_inputs( ['Tile_MemCore-bc.db'] )

  e2e_apps = ["tests/conv_3_3", "apps/cascade", "apps/harris_auto", "apps/resnet_i1_o1_mem", "apps/resnet_i1_o1_pond"]

  # Only use these steps with power domains off and no flattening...
  use_e2e = False
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
    step.extend_inputs( ['Tile_PE-typical.lib', 'Tile_PE-bc.lib', 'Tile_PE.lef'] )
    step.extend_inputs( ['Tile_MemCore-typical.lib', 'Tile_MemCore-bc.lib', 'Tile_MemCore.lef'] )

  # Need the netlist and SDF files for gate-level sim

  vcs_sim.extend_inputs( ['Tile_PE.vcs.v', 'Tile_PE.sdf'] )
  vcs_sim.extend_inputs( ['Tile_MemCore.vcs.v', 'Tile_MemCore.sdf'] )

  # Need the cgra tile OASIS to merge into the final layout

  signoff.extend_inputs( ['Tile_PE.oas'] )
  signoff.extend_inputs( ['Tile_MemCore.oas'] )

  # Need LVS verilog files for both tile types to do LVS

  lvs.extend_inputs( ['Tile_PE.lvs.v'] )
  lvs.extend_inputs( ['Tile_MemCore.lvs.v'] )
  
  # Need sram spice file for LVS

  lvs.extend_inputs( ['sram.spi'] )

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  cts.extend_inputs( custom_cts.all_outputs() )

  # SDC hack for the genlibdb and pt_signoff steps
  genlibdb_tt.extend_inputs( custom_hack_sdc_unit.all_outputs() )
  genlibdb_ff.extend_inputs( custom_hack_sdc_unit.all_outputs() )
  pt_signoff.extend_inputs( custom_hack_sdc_unit.all_outputs() )
  
  # Inputs
  g.add_input( 'design.v', rtl.i('design.v') )
  g.add_input( 'header'  , rtl.i('header')   )

  # Outputs
  g.add_output( 'tile_array-typical.lib',      genlibdb_tt.o('design.lib')        )
  g.add_output( 'tile_array-typical.db',       genlibdb_tt.o('design.db')         )
  g.add_output( 'tile_array-bc.lib',           genlibdb_ff.o('design.lib')        )
  g.add_output( 'tile_array-bc.db',            genlibdb_ff.o('design.db')         )
  g.add_output( 'tile_array.lef',              signoff.o('design.lef')            )
  g.add_output( 'tile_array.vcs.v',            signoff.o('design.vcs.v')          )
  g.add_output( 'tile_array.sdf',              signoff.o('design.sdf')            )
  g.add_output( 'tile_array.oas',              signoff.o('design-merged.oas')     )
  g.add_output( 'tile_array.lvs.v',            lvs.o('design_merged.lvs.v')       )
  g.add_output( 'tile_array.vcs.pg.v',         signoff.o('design.vcs.pg.v')       )
  g.add_output( 'tile_array.spef.gz',          signoff.o('design.spef.gz')        )
  g.add_output( 'tile_array_sram.spi',         Tile_MemCore.o('Tile_MemCore_sram.spi')         )
  g.add_output( 'tile_array_sram.v',           Tile_MemCore.o('Tile_MemCore_sram.v')           )
  g.add_output( 'tile_array_sram-bc.db',       Tile_MemCore.o('Tile_MemCore_sram-bc.db')       )
  g.add_output( 'tile_array_sram-bc.lib',      Tile_MemCore.o('Tile_MemCore_sram-bc.lib')      )
  g.add_output( 'tile_array_sram-wc.db',       Tile_MemCore.o('Tile_MemCore_sram-wc.db')       )
  g.add_output( 'tile_array_sram-wc.lib',      Tile_MemCore.o('Tile_MemCore_sram-wc.lib')      )
  g.add_output( 'tile_array_sram-typical.db',  Tile_MemCore.o('Tile_MemCore_sram-typical.db')  )
  g.add_output( 'tile_array_sram-typical.lib', Tile_MemCore.o('Tile_MemCore_sram-typical.lib') )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info           )
  g.add_step( rtl            )
  g.add_step( Tile_MemCore   )
  g.add_step( Tile_PE        )
  g.add_step( constraints    )
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
  g.add_step( drc            )
  g.add_step( lvs            )
  g.add_step( debugcalibre   )
  g.add_step( gls_args       )
  g.add_step( testbench      )
  g.add_step( vcs_sim        )
  g.add_step( genlibdb_tt    )
  g.add_step( genlibdb_ff    )
  g.add_step( custom_hack_sdc_unit )

  if use_e2e:
    for app in e2e_apps:
        g.add_step( e2e_tb_nodes[app]    )
        g.add_step( e2e_sim_nodes[app]   )
        g.add_step( e2e_power_nodes[app] )
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
      g.connect_by_name( Tile_MemCore,      drc            )
      g.connect_by_name( Tile_MemCore,      lvs            )
      g.connect_by_name( Tile_MemCore,      vcs_sim        )
      g.connect_by_name( Tile_MemCore,      genlibdb_tt    )
      g.connect_by_name( Tile_MemCore,      genlibdb_ff    )

  # inputs to Tile_PE
  g.connect_by_name( rtl, Tile_PE )
  # outputs from Tile_PE
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
  g.connect_by_name( Tile_PE,      drc            )
  g.connect_by_name( Tile_PE,      lvs            )
  g.connect_by_name( Tile_PE,      genlibdb_tt    )
  g.connect_by_name( Tile_PE,      genlibdb_ff    )

  g.connect_by_name( rtl,            synth        )
  g.connect_by_name( rtl,            synth        )
  g.connect_by_name( constraints,    synth        )

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

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )

  g.connect_by_name( adk,          genlibdb_tt )
  g.connect_by_name( adk,          genlibdb_ff )
  g.connect_by_name( signoff,      genlibdb_tt )
  g.connect_by_name( signoff,      genlibdb_ff )

  g.connect_by_name( adk,      debugcalibre )
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

  # SDC hack for the genlibdb and pt_signoff steps
  g.connect_by_name( custom_hack_sdc_unit, genlibdb_tt )
  g.connect_by_name( custom_hack_sdc_unit, genlibdb_ff )
  g.connect_by_name( custom_hack_sdc_unit, pt_signoff )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  # Init needs pipeline params for floorplanning
  init.update_params({ 'pipeline_config_interval': parameters['pipeline_config_interval'] }, True)
  
  # CTS uses height/width param to do CTS endpoint overrides properly
  cts.update_params({ 'array_width':  parameters['array_width']}, True)
  cts.update_params({ 'array_height':  parameters['array_height']}, True)

  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

  # genlibdb parameters
  genlibdb_order = [
    'read_design.tcl',
    'extract_model.tcl'
  ]
  genlibdb_tt.update_params({
    'corner': 'typical',
    'order': genlibdb_order
  })
  genlibdb_ff.update_params({
    'corner': 'bc',
    'order': genlibdb_order
  })

  # Add SDC unit hack before genlibdb and pt_signoff
  sdc_hack_command = "python inputs/hack_sdc_unit.py inputs/design.pt.sdc"

  # The SDC file generated by Innovus contains -library flag to explicitly
  # specify which library to use for the cell. However, we will change the
  # target library for different corners and that makes the SDC commands
  # fail to find the cell. We should remove the -library flag and let the
  # tool find the cell from the target library (default behavior).
  sdc_filter_command = "sed -i 's/-library [^ ]* //g' inputs/design.pt.sdc"

  # add the commands to the steps
  genlibdb_tt.pre_extend_commands( [sdc_hack_command, sdc_filter_command] )
  genlibdb_ff.pre_extend_commands( [sdc_hack_command, sdc_filter_command] )
  pt_signoff.pre_extend_commands( [sdc_hack_command, sdc_filter_command] )

  # init -- update custom order
  init.update_params( { 'order': init_order } )

  # DRC Rule Decks
  drc_rule_decks = [
    "antenna",
    "collat",
    "drc-drcd",
    "drc-lu",
    # "drc-denall"
    # "drc-cden-lden-collat",
    # "drc-fullchip",
    # "tapein"
  ]
  drc.update_params( {'rule_decks': drc_rule_decks } )
  
  # We are overriding certain pin types for CTS, so we need to
  # add the script that does that to the CTS order
  order = cts.get_param('order')
  main_idx = order.index( 'main.tcl' )
  order.insert( main_idx, 'cts-overrides.tcl' )
  cts.update_params( { 'order': order } )

  synth_postconditions = synth.get_postconditions()
  for postcon in synth_postconditions:
      if 'percent_clock_gated' in postcon:
          synth_postconditions.remove(postcon)
  synth.set_postconditions( synth_postconditions )

  return g

if __name__ == '__main__':
  g = construct()
#  g.plot()


