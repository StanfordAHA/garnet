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

  adk_name = get_sys_adk()  # E.g. 'gf12-adk' or 'tsmc16'
  adk_view = 'multivt'
  which_soc = 'onyx-intel16'

  parameters = {
    'construct_path'           : __file__,
    'design_name'              : 'GarnetSOC_pad_frame',
    'clock_period'             : 1.6 * 1000,
    'adk'                      : adk_name,
    'adk_view'                 : adk_view,
    'adk_stdcell'              : 'b15_7t_108pp',
    'adk_libmodel'             : 'nldm',
    # Synthesis
    'flatten_effort'           : 3,
    'topographical'            : True,
    # RTL Generation
    'array_width'              : 28,
    'array_height'             : 16,
    'num_glb_tiles'            : 14,
    'interconnect_only'        : False,
    'use_local_garnet'         : False,
    # glb tile memory size (unit: KB)
    'glb_tile_mem_size'        : 128,
    # Power Domains
    'PWR_AWARE'                : False,
    # Include Garnet?
    'soc_only'                 : False,
    # Include SoC core? (use 0 for false, 1 for true)
    'include_core'             : 1,
    # Low Effort flow
    'express_flow'             : False,
    'skip_verify_connectivity' : True,
    # Hold fixing
    'signoff_engine'           : True,
    'hold_target_slack'        : 0.100,
    # TLX Ports Partitions
    'TLX_FWD_DATA_LO_WIDTH'    : 16,
    'TLX_REV_DATA_LO_WIDTH'    : 45,
    'nthreads'                 : 16,
    # Testbench
    'cgra_apps'                : ["tests/conv_1_2", "tests/conv_2_1"]
  }

  # Four 32KB SRAM macros connected to the NIC400 bus
  params_sram_nic = {
    # SRAM macros
    'num_words'         : 4096,
    'word_size'         : 64,
    'mux_size'          : 4,
    'partial_write'     : 1,
  }

  # One logical 128KB memory connected directly to the CPU
  # Due to the max word size limitation in this technology
  # We stack four 32KB SRAMs to implement this 128KB memory
  params_sram_cpu = {
    # SRAM macros
    'num_words'         : 8192,
    'word_size'         : 32,
    'mux_size'          : 8,
    'partial_write'     : 1,
  }

  init_order = [
      'pre-init.tcl',
      'main.tcl',
      'innovus-pnr-config.tcl',
      'dont-use.tcl',
      'quality-of-life.tcl',
      'stylus-compatibility-procs.tcl',
      'floorplan.tcl',
      'create-rows.tcl',
      'add-tracks.tcl',
      # 'place-dic-cells-tma2.tcl',
      # 'gen-bumps.tcl', # TODO: turn-off for TMA2
      # 'route-bumps.tcl', # TODO: turn-off for TMA2
      'place-macros.tcl',
      'add-welltaps-for-pad-latchup.tcl',
      'create-special-grid.tcl',
      'carve-out-special-grid-fullchip.tcl',
      'io-fillers.tcl'
  ]
  
  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step
  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps
  rtl            = Step( f'{this_dir}/../common/rtl'                   )
  soc_rtl        = Step( f'{this_dir}/../common/soc-rtl-v2'            )
  gen_sram_nic   = Step( f'{this_dir}/../common/gen_sram_macro'        )
  gen_sram_cpu   = Step( f'{this_dir}/../common/gen_sram_macro'        )
  read_design    = Step( f'{this_dir}/../common/fc-custom-read-design' )
  custom_power   = Step( f'{this_dir}/../common/custom-power-chip'     )
  init_fc        = Step( f'{this_dir}/../common/init-fullchip'         )
  constraints    = Step( f'{this_dir}/constraints'                     )
  custom_init    = Step( f'{this_dir}/custom-init'                     )
  custom_cts     = Step( f'{this_dir}/custom-cts'                      )
  io_file        = Step( f'{this_dir}/io_file'                         )
  # Rename the SRAM generation nodes
  gen_sram_nic.set_name( 'gen_sram_macro_nic' )
  gen_sram_cpu.set_name( 'gen_sram_macro_cpu' )

  # Block-level designs
  tile_array   = Subgraph(f'{this_dir}/../tile_array',             'tile_array')
  glb_top      = Subgraph(f'{this_dir}/../glb_top',                'glb_top')
  tapeout_flow = Subgraph(f'{this_dir}/../intel-usp-tapeout-flow', 'tapeout-flow')

  # CGRA simulation
  cgra_rtl_sim_compile  = Step( f'{this_dir}/cgra_rtl_sim_compile' )
  cgra_rtl_sim_run      = Step( f'{this_dir}/cgra_rtl_sim_run'     )
  cgra_sim_build        = Step( f'{this_dir}/cgra_sim_build'       )
  # cgra_gl_sim_compile   = Step( this_dir + '/cgra_gl_sim_compile'  )
  # cgra_gl_sim_run       = Step( this_dir + '/cgra_gl_sim_run'      )
  # cgra_gl_ptpx          = Step( this_dir + '/cgra_gl_ptpx'         )
  # cgra_rtl_sim_verdict  = Step( this_dir + '/cgra_rtl_sim_verdict' )
  # cgra_gl_sim_verdict   = Step( this_dir + '/cgra_gl_sim_verdict'  )

  # Default steps
  synth          = Step( 'cadence-genus-synthesis',          default=True )
  info           = Step( 'info',                             default=True )
  iflow          = Step( 'cadence-innovus-flowsetup',        default=True )
  init           = Step( 'cadence-innovus-init',             default=True )
  power          = Step( 'cadence-innovus-power',            default=True )
  place          = Step( 'cadence-innovus-place',            default=True )
  cts            = Step( 'cadence-innovus-cts',              default=True )
  postcts_hold   = Step( 'cadence-innovus-postcts_hold',     default=True )
  route          = Step( 'cadence-innovus-route',            default=True )
  postroute      = Step( 'cadence-innovus-postroute',        default=True )
  postroute_hold = Step( 'cadence-innovus-postroute_hold',   default=True )
  signoff        = Step( 'cadence-innovus-signoff',          default=True )
  pt_signoff     = Step( 'synopsys-pt-timing-signoff',       default=True )
  debugcalibre   = Step( 'cadence-innovus-debug-calibre',    default=True )

  # These steps need timing info for cgra tiles
  hier_steps = [
    synth,
    iflow,
    init,
    power,
    place,
    cts,
    postcts_hold,
    route,
    postroute,
    postroute_hold,
    signoff
  ]
  for step in hier_steps:
    step.extend_inputs( ['tile_array-typical.lib', 'tile_array-bc.lib', 'tile_array.lef'] )
    step.extend_inputs( ['glb_top-typical.lib',    'glb_top-bc.lib',    'glb_top.lef'] )
    step.extend_inputs( ['sram_nic-typical.lib',   'sram_nic-bc.lib',   'sram_nic.lef'] )
    step.extend_inputs( ['sram_cpu-typical.lib',   'sram_cpu-bc.lib',   'sram_cpu.lef'] )
  
  # PTPX Signoff needs .db files only
  pt_signoff.extend_inputs( ['tile_array-typical.db', 'tile_array-bc.db'] )
  pt_signoff.extend_inputs( ['glb_top-typical.db',    'glb_top-bc.db'] )
  pt_signoff.extend_inputs( ['sram_nic-typical.db',   'sram_nic-bc.db'] )
  pt_signoff.extend_inputs( ['sram_cpu-typical.db',   'sram_cpu-bc.db'] )

  # Need all block oasis's to merge into the final layout
  signoff.extend_inputs( ['tile_array.oas'] )
  signoff.extend_inputs( ['glb_top.oas'] )
  signoff.extend_inputs( ['sram_nic.oas'] )
  signoff.extend_inputs( ['sram_cpu.oas'] )

  # Add extra input edges to innovus steps that need custom tweaks
  init.extend_inputs( custom_init.all_outputs() )
  init.extend_inputs( init_fc.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  # TODO: Disable custom CTS for now
  #       Understand it and turn it back up later
  # cts.extend_inputs( custom_cts.all_outputs() )

  synth.extend_inputs( soc_rtl.all_outputs() )
  synth.extend_inputs( read_design.all_outputs() )
  synth.extend_inputs( ["cons_scripts"] )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info              )
  g.add_step( rtl               )
  g.add_step( soc_rtl           )
  g.add_step( gen_sram_nic      )
  g.add_step( gen_sram_cpu      )
  g.add_step( tile_array        )
  g.add_step( glb_top           )
  g.add_step( constraints       )
  g.add_step( read_design       )
  g.add_step( synth             )
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
  g.add_step( route             )
  g.add_step( postroute         )
  g.add_step( postroute_hold    )
  g.add_step( signoff           )
  g.add_step( pt_signoff        )
  g.add_step( debugcalibre      )
  g.add_step( tapeout_flow      )

  # App test nodes
  g.add_step( cgra_rtl_sim_compile )
  g.add_step( cgra_sim_build       )
  g.add_step( cgra_rtl_sim_run     )
  g.add_step( custom_cts        )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( adk,      gen_sram_nic   )
  g.connect_by_name( adk,      gen_sram_cpu   )
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
  # Connect RTL verification nodes
  g.connect_by_name( rtl, cgra_rtl_sim_compile )
  g.connect_by_name( cgra_sim_build, cgra_rtl_sim_run )
  g.connect_by_name( cgra_rtl_sim_compile, cgra_rtl_sim_run )

  # Connect GL verification nodes
  # g.connect_by_name( signoff, cgra_gl_sim_compile )

  # All of the blocks within this hierarchical design
  # Skip these if we're doing soc_only
  if parameters['soc_only'] == False:
      blocks = [tile_array, glb_top]
      for block in blocks:
          g.connect_by_name( block, synth          )
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
      # Tile_array can use rtl from rtl node
      g.connect_by_name( rtl, tile_array )
      # glb_top can use rtl from rtl node
      g.connect_by_name( rtl, glb_top )

  g.connect_by_name( rtl,          synth          )
  g.connect_by_name( soc_rtl,      synth          )
  g.connect_by_name( constraints,  synth          )
  g.connect_by_name( read_design,  synth          )
  g.connect_by_name( soc_rtl,      io_file        )
  g.connect_by_name( synth,        iflow          )
  g.connect_by_name( synth,        init           )
  g.connect_by_name( synth,        power          )
  g.connect_by_name( synth,        place          )
  g.connect_by_name( synth,        cts            )
  g.connect_by_name( iflow,        init           )
  g.connect_by_name( iflow,        power          )
  g.connect_by_name( iflow,        place          )
  g.connect_by_name( iflow,        cts            )
  g.connect_by_name( iflow,        postcts_hold   )
  g.connect_by_name( iflow,        route          )
  g.connect_by_name( iflow,        postroute      )
  g.connect_by_name( iflow,        postroute_hold )
  g.connect_by_name( iflow,        signoff        )
  g.connect_by_name( custom_init,  init           )
  g.connect_by_name( custom_power, power          )
  g.connect_by_name( custom_cts,   cts            )

  # Connect gen_sram_macro node(s) to all downstream nodes that need them
  sram_nodes = [synth, iflow, init, power, place, cts, postcts_hold,
                route, postroute, postroute_hold, signoff, pt_signoff]
  for node in sram_nodes:
    for sram_output in gen_sram_nic.all_outputs():
      node_input = sram_output.replace('sram', 'sram_nic')
      if node_input in node.all_inputs():
        g.connect(gen_sram_nic.o(sram_output), node.i(node_input))
    for sram_output in gen_sram_cpu.all_outputs():
      node_input = sram_output.replace('sram', 'sram_cpu')
      if node_input in node.all_inputs():
        g.connect(gen_sram_cpu.o(sram_output), node.i(node_input))

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

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( synth,    debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  # Allow user to override parms with env in a limited sort of way
  g.update_params( parameters )

  # Provide different parameter set to second sram node, so it can actually 
  # generate a different sram
  gen_sram_nic.update_params( params_sram_nic )
  gen_sram_cpu.update_params( params_sram_cpu )

  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

  # DC needs these param to set the NO_CGRA macro
  synth.update_params({'soc_only': parameters['soc_only']}, True)
  # DC needs these params to set macros in soc rtl
  synth.update_params({'TLX_FWD_DATA_LO_WIDTH' : parameters['TLX_FWD_DATA_LO_WIDTH']}, True)
  synth.update_params({'TLX_REV_DATA_LO_WIDTH' : parameters['TLX_REV_DATA_LO_WIDTH']}, True)
  init.update_params({'soc_only': parameters['soc_only']}, True)

  init.update_params( {'order': init_order } )

  # glb_top parameters update
  glb_top.update_params({'array_width': parameters['array_width']}, True)
  glb_top.update_params({'glb_tile_mem_size': parameters['glb_tile_mem_size']}, True)
  glb_top.update_params({'num_glb_tiles': parameters['num_glb_tiles']}, True)

  # App test parameters update
  cgra_rtl_sim_compile.update_params({'array_width': parameters['array_width']}, True)
  cgra_rtl_sim_compile.update_params({'array_height': parameters['array_height']}, True)
  cgra_rtl_sim_compile.update_params({'clock_period': parameters['clock_period']}, True)
  cgra_rtl_sim_compile.update_params({'glb_tile_mem_size': parameters['glb_tile_mem_size']}, True)

  cgra_rtl_sim_run.update_params({'cgra_apps': parameters['cgra_apps']}, True)

  # Power node order manipulation
  order = power.get_param('order')
  # Move endcap/welltap insertion to end of power step to improve runtime
  order.insert(0, 'add-endcaps-welltaps.tcl' )
  power.update_params( { 'order': order } )
  
  # connect tapeout
  g.connect(signoff.o("design-merged.oas"), tapeout_flow.i("design.oas"))

  return g

if __name__ == '__main__':
  g = construct()
#  g.plot()
