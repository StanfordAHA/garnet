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
    'clock_period'             : 2.5 * 1000,
    'adk'                      : adk_name,
    'adk_view'                 : adk_view,
    'adk_stdcell'              : 'b0m_6t_108pp',
    'adk_libmodel'             : 'nldm',
    # Synthesis
    'flatten_effort'           : 3,
    'topographical'            : True,
    # CTS
    'useful_skew'              : True,
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
    # Pipeline stage insertion
    'pipeline_config_interval' : 8
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
      'dont-use.tcl',
      'quality-of-life.tcl',
      'stylus-compatibility-procs.tcl',
      'floorplan.tcl',
      'io_pad_placement.tcl',
      'create-route-blockage-io-pads.tcl',
      'io-fillers.tcl',
      'create-rows.tcl',
      'add-tracks.tcl',
      'gen-bumps.tcl',
      'route-bumps.tcl',
      'innovus-pnr-config.tcl',
      'place-soc-mem.tcl',
      'place-glb-top.tcl',
      'place-io-tile.tcl',
      'place-matrix-unit.tcl',
      'place-tile-array.tcl',
      'add-welltaps-for-pad-latchup.tcl',
      'create-special-grid.tcl',
      'carve-out-special-grid-fullchip.tcl'
  ]
  
  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step
  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps
  rtl                  = Step( f'{this_dir}/../common/rtl'                      )
  soc_rtl              = Step( f'{this_dir}/../common/soc-rtl-v2'               )
  gen_sram_nic         = Step( f'{this_dir}/../common/gen_sram_macro'           )
  gen_sram_cpu         = Step( f'{this_dir}/../common/gen_sram_macro'           )
  read_design          = Step( f'{this_dir}/../common/fc-custom-read-design'    )
  custom_power         = Step( f'{this_dir}/custom-power-chip'                  )
  constraints          = Step( f'{this_dir}/constraints'                        )
  custom_init          = Step( f'{this_dir}/custom-init'                        )
  custom_cts           = Step( f'{this_dir}/custom-cts'                         )
  custom_pre_signoff   = Step( f'{this_dir}/custom-pre-signoff'                 )
  lvs                  = Step( f'{this_dir}/../common/intel16-synopsys-icv-lvs' )
  custom_flowgen_setup = Step( f'{this_dir}/custom-flowgen-setup'               )
  custom_signoff       = Step( f'{this_dir}/custom-signoff'                     )
  custom_hack_sdc_unit = Step( f'{this_dir}/../common/custom-hack-sdc-unit'     )
  # Rename the SRAM generation nodes
  gen_sram_nic.set_name( 'gen_sram_macro_nic' )
  gen_sram_cpu.set_name( 'gen_sram_macro_cpu' )

  # Block-level designs
  Tile_IOCoreReadyValid = Subgraph(f'{this_dir}/../Tile_IOCoreReadyValid',  'Tile_IOCoreReadyValid')
  Tile_PE               = Subgraph(f'{this_dir}/../Tile_PE',                'Tile_PE'              )
  Tile_MemCore          = Subgraph(f'{this_dir}/../Tile_MemCore',           'Tile_MemCore'         )
  global_buffer         = Subgraph(f'{this_dir}/../glb_top',                'glb_top'              )
  matrix_unit           = Subgraph(f'{this_dir}/../MatrixUnit',             'MatrixUnit'           )
  tapeout_flow          = Subgraph(f'{this_dir}/../intel-usp-tapeout-flow', 'tapeout-flow'         )

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
  pt_signoff_flat= Step( 'synopsys-pt-timing-signoff-flat',  default=True )
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
    step.extend_inputs( ['Tile_IOCoreReadyValid-typical.lib', 'Tile_IOCoreReadyValid-bc.lib', 'Tile_IOCoreReadyValid.lef'] )
    step.extend_inputs( ['Tile_PE-typical.lib',               'Tile_PE-bc.lib',               'Tile_PE.lef'] )
    step.extend_inputs( ['Tile_MemCore-typical.lib',          'Tile_MemCore-bc.lib',          'Tile_MemCore.lef'] )
    step.extend_inputs( ['global_buffer-typical.lib',         'global_buffer-bc.lib',         'global_buffer.lef'] )
    step.extend_inputs( ['MatrixUnitWrapper-typical.lib',     'MatrixUnitWrapper-bc.lib',     'MatrixUnitWrapper.lef'] )
    step.extend_inputs( ['sram_nic-typical.lib',              'sram_nic-bc.lib',              'sram_nic.lef'] )
    step.extend_inputs( ['sram_cpu-typical.lib',              'sram_cpu-bc.lib',              'sram_cpu.lef'] )
  
  # PTPX Signoff needs .db files only
  pt_signoff.extend_inputs( ['Tile_IOCoreReadyValid-typical.db', 'Tile_IOCoreReadyValid-bc.db'] )
  pt_signoff.extend_inputs( ['Tile_PE-typical.db',               'Tile_PE-bc.db'] )
  pt_signoff.extend_inputs( ['Tile_MemCore-typical.db',          'Tile_MemCore-bc.db'] )
  pt_signoff.extend_inputs( ['global_buffer-typical.db',         'global_buffer-bc.db'] )
  pt_signoff.extend_inputs( ['MatrixUnitWrapper-typical.db',     'MatrixUnitWrapper-bc.db'] )
  pt_signoff.extend_inputs( ['sram_nic-typical.db',              'sram_nic-bc.db'] )
  pt_signoff.extend_inputs( ['sram_cpu-typical.db',              'sram_cpu-bc.db'] )

  pt_signoff_flat.extend_inputs( ['Tile_IOCoreReadyValid.vcs.v', 'Tile_IOCoreReadyValid.pt.sdc', 'Tile_IOCoreReadyValid.spef.gz'] )
  pt_signoff_flat.extend_inputs( ['Tile_PE.vcs.v',               'Tile_PE.pt.sdc',               'Tile_PE.spef.gz'              ] )
  pt_signoff_flat.extend_inputs( ['Tile_MemCore.vcs.v',          'Tile_MemCore.pt.sdc',          'Tile_MemCore.spef.gz'         ] )
  pt_signoff_flat.extend_inputs( ['global_buffer.vcs.v',         'global_buffer.pt.sdc',         'global_buffer.spef.gz'        ] )
  pt_signoff_flat.extend_inputs( ['MatrixUnitWrapper.vcs.v',     'MatrixUnitWrapper.pt.sdc',     'MatrixUnitWrapper.spef.gz'    ] )
  pt_signoff_flat.extend_inputs( ['sram_nic-typical.db',         'sram_nic-bc.db'] )
  pt_signoff_flat.extend_inputs( ['sram_cpu-typical.db',         'sram_cpu-bc.db'] )
  pt_signoff_flat.extend_inputs( ['Tile_MemCore_sram-typical.db','Tile_MemCore_sram-bc.db'] )
  pt_signoff_flat.extend_inputs( ['global_buffer_sram-typical.db','global_buffer_sram-bc.db'] )
  pt_signoff_flat.extend_inputs( ['MatrixUnitWrapper_sram_iw-typical.db',   'MatrixUnitWrapper_sram_iw-bc.db'] )
  pt_signoff_flat.extend_inputs( ['MatrixUnitWrapper_sram_accum-typical.db','MatrixUnitWrapper_sram_accum-bc.db'] )
  pt_signoff_flat.extend_inputs( ['MatrixUnitWrapper_sram_si-typical.db',   'MatrixUnitWrapper_sram_si-bc.db'] )
  pt_signoff_flat.extend_inputs( ['MatrixUnitWrapper_sram_sw-typical.db',   'MatrixUnitWrapper_sram_sw-bc.db'] )

  # Need all block oasis's to merge into the final layout
  signoff.extend_inputs( ['Tile_IOCoreReadyValid.oas'] )
  signoff.extend_inputs( ['Tile_PE.oas'] )
  signoff.extend_inputs( ['Tile_MemCore.oas'] )
  signoff.extend_inputs( ['global_buffer.oas'] )
  signoff.extend_inputs( ['MatrixUnitWrapper.oas'] )
  signoff.extend_inputs( ['sram_nic.oas'] )
  signoff.extend_inputs( ['sram_cpu.oas'] )
  signoff.extend_inputs( custom_pre_signoff.all_outputs() )

  # Add extra input edges to innovus steps that need custom tweaks
  iflow.extend_inputs( custom_flowgen_setup.all_outputs() )
  init.extend_inputs( custom_init.all_outputs() )
  init.extend_inputs( ['io_pad_placement.tcl'] )
  # init.extend_inputs( init_fc.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  cts.extend_inputs( custom_cts.all_outputs() )

  synth.extend_inputs( ['rtl', 'rtl-scripts'] )
  synth.extend_inputs( read_design.all_outputs() )
  synth.extend_inputs( ["cons_scripts"] )

  # Need LVS verilog files for both tile types to do LVS
  lvs.extend_inputs( ['Tile_IOCoreReadyValid.lvs.v'] )
  lvs.extend_inputs( ['Tile_PE.lvs.v'] )
  lvs.extend_inputs( ['Tile_MemCore.lvs.v'] )
  lvs.extend_inputs( ['global_buffer.lvs.v'] )
  lvs.extend_inputs( ['MatrixUnitWrapper.lvs.v'] )

  # Need sram spice file for LVS
  lvs.extend_inputs( ['global_buffer_sram.spi'] )
  lvs.extend_inputs( ['Tile_MemCore_sram.spi'] )
  lvs.extend_inputs( ['MatrixUnitWrapper_sram_accum.spi'] )
  lvs.extend_inputs( ['MatrixUnitWrapper_sram_iw.spi'] )
  lvs.extend_inputs( ['MatrixUnitWrapper_sram_si.spi'] )
  lvs.extend_inputs( ['MatrixUnitWrapper_sram_sw.spi'] )

  # signoff extend inputs
  signoff.extend_inputs( custom_signoff.all_outputs() )

  # SDC hack for the genlibdb and pt_signoff steps
  pt_signoff.extend_inputs( custom_hack_sdc_unit.all_outputs() )
  pt_signoff_flat.extend_inputs( custom_hack_sdc_unit.all_outputs() )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info                  )
  g.add_step( rtl                   )
  g.add_step( soc_rtl               )
  g.add_step( gen_sram_nic          )
  g.add_step( gen_sram_cpu          )
  g.add_step( Tile_IOCoreReadyValid )
  g.add_step( Tile_PE               )
  g.add_step( Tile_MemCore          )
  g.add_step( global_buffer         )
  g.add_step( matrix_unit           )
  g.add_step( constraints           )
  g.add_step( read_design           )
  g.add_step( synth                 )
  g.add_step( custom_flowgen_setup  )
  g.add_step( custom_signoff        )
  g.add_step( custom_pre_signoff    )
  g.add_step( iflow                 )
  g.add_step( init                  )
  g.add_step( custom_init           )
  g.add_step( power                 )
  g.add_step( custom_power          )
  g.add_step( place                 )
  g.add_step( cts                   )
  g.add_step( postcts_hold          )
  g.add_step( route                 )
  g.add_step( postroute             )
  g.add_step( postroute_hold        )
  g.add_step( signoff               )
  g.add_step( pt_signoff            )
  g.add_step( pt_signoff_flat       )
  g.add_step( debugcalibre          )
  g.add_step( lvs                   )
  g.add_step( tapeout_flow          )
  g.add_step( custom_hack_sdc_unit  )

  # App test nodes
  g.add_step( custom_cts            )

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
  g.connect_by_name( adk,      lvs            )

  # All of the blocks within this hierarchical design
  # Skip these if we're doing soc_only
  if parameters['soc_only'] == False:
      blocks = [Tile_IOCoreReadyValid, Tile_PE, Tile_MemCore, global_buffer, matrix_unit]
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
          g.connect_by_name( block, pt_signoff_flat)
          g.connect_by_name( block, lvs            )
      # These subgraphs can inherit the RTL from the top level
      g.connect_by_name( rtl, Tile_IOCoreReadyValid )
      g.connect_by_name( rtl, Tile_PE               )
      g.connect_by_name( rtl, Tile_MemCore          )
      g.connect_by_name( rtl, global_buffer         )
      g.connect_by_name( rtl, matrix_unit           )

  g.connect_by_name( rtl,          synth          )
  g.connect_by_name( soc_rtl,      synth          )
  g.connect_by_name( constraints,  synth          )
  g.connect_by_name( read_design,  synth          )
  # g.connect_by_name( soc_rtl,      io_file        )
  g.connect_by_name( soc_rtl,      init           ) # feed the io_pad_placement.tcl to init
  g.connect_by_name( synth,        iflow          )
  g.connect_by_name( synth,        init           )
  g.connect_by_name( synth,        power          )
  g.connect_by_name( synth,        place          )
  g.connect_by_name( synth,        cts            )
  g.connect_by_name( custom_flowgen_setup,  iflow )
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
                route, postroute, postroute_hold, signoff, pt_signoff, pt_signoff_flat]
  for node in sram_nodes:
    for sram_output in gen_sram_nic.all_outputs():
      node_input = sram_output.replace('sram', 'sram_nic')
      if node_input in node.all_inputs():
        g.connect(gen_sram_nic.o(sram_output), node.i(node_input))
    for sram_output in gen_sram_cpu.all_outputs():
      node_input = sram_output.replace('sram', 'sram_cpu')
      if node_input in node.all_inputs():
        g.connect(gen_sram_cpu.o(sram_output), node.i(node_input))
  
  # Connect SRAMs to LVS nodes
  lvs.extend_inputs( ['sram_nic.spi', 'sram_cpu.spi'] )
  g.connect(gen_sram_nic.o('sram.spi'), lvs.i('sram_nic.spi'))
  g.connect(gen_sram_cpu.o('sram.spi'), lvs.i('sram_cpu.spi'))

  g.connect_by_name( init,           power          )
  g.connect_by_name( power,          place          )
  g.connect_by_name( place,          cts            )
  g.connect_by_name( cts,            postcts_hold   )
  g.connect_by_name( postcts_hold,   route          )
  g.connect_by_name( route,          postroute      )
  g.connect_by_name( postroute,      postroute_hold )
  g.connect_by_name( postroute_hold, signoff        )
  g.connect_by_name( custom_signoff, signoff        )
  g.connect_by_name( custom_pre_signoff,   signoff  )

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )
  g.connect_by_name( adk,          pt_signoff_flat   )
  g.connect_by_name( signoff,      pt_signoff_flat   )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( synth,    debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( signoff,  lvs          )

  # SDC hack for the genlibdb and pt_signoff steps
  g.connect_by_name( custom_hack_sdc_unit, pt_signoff )
  g.connect_by_name( custom_hack_sdc_unit, pt_signoff_flat )

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
  init.update_params( {'pipeline_config_interval': parameters['pipeline_config_interval']}, True )

  # global_buffer parameters update
  global_buffer.update_params({'array_width': parameters['array_width']}, True)
  global_buffer.update_params({'glb_tile_mem_size': parameters['glb_tile_mem_size']}, True)
  global_buffer.update_params({'num_glb_tiles': parameters['num_glb_tiles']}, True)

  postroute_hold.update_params({'full_chip_build': True}, True)

  # Power node order manipulation
  order = power.get_param('order')
  # Move endcap/welltap insertion to end of power step to improve runtime
  order.insert(0, 'add-endcaps-welltaps.tcl' )
  power.update_params( { 'order': order } )

  # update clock insertion delay in CTS
  order = cts.get_param( 'order' )
  order.insert(order.index('main.tcl'), 'custom-cts-additional-setup.tcl')
  cts.set_param( 'order', order )

  # add custom signoff create physical pin script
  order = signoff.get_param('order')
  order.insert(0, 'create-physical-pin.tcl' )
  order = ['pre-signoff.tcl'] + order
  signoff.update_params( { 'order': order } )
  
  # connect tapeout
  g.connect(signoff.o("design-merged.oas"), tapeout_flow.i("design.oas"))

  # Add SDC unit hack before genlibdb and pt_signoff
  sdc_hack_command = "python inputs/hack_sdc_unit.py inputs/design.pt.sdc"

  # The SDC file generated by Innovus contains -library flag to explicitly
  # specify which library to use for the cell. However, we will change the
  # target library for different corners and that makes the SDC commands
  # fail to find the cell. We should remove the -library flag and let the
  # tool find the cell from the target library (default behavior).
  sdc_filter_command = "sed -i 's/-library [^ ]* //g' inputs/design.pt.sdc"

  # adding propagaed_clock command in the sdc file
  sdc_pclock_command = 'echo "\nset_propagated_clock [all_clocks]\n" >> inputs/design.pt.sdc' 

  # add the commands to the steps
  pt_signoff.pre_extend_commands( [sdc_hack_command, sdc_filter_command, sdc_pclock_command] )

  pt_signoff_flat.pre_extend_commands( [
    "python inputs/hack_sdc_unit.py inputs/design.pt.sdc",
    "sed -i 's/-library [^ ]* //g'  inputs/design.pt.sdc",
    "python inputs/hack_sdc_unit.py inputs/MatrixUnitWrapper.pt.sdc",
    "sed -i 's/-library [^ ]* //g'  inputs/MatrixUnitWrapper.pt.sdc",
    "python inputs/hack_sdc_unit.py inputs/Tile_IOCoreReadyValid.pt.sdc",
    "sed -i 's/-library [^ ]* //g'  inputs/Tile_IOCoreReadyValid.pt.sdc",
    "python inputs/hack_sdc_unit.py inputs/Tile_PE.pt.sdc",
    "sed -i 's/-library [^ ]* //g'  inputs/Tile_PE.pt.sdc",
    "python inputs/hack_sdc_unit.py inputs/Tile_MemCore.pt.sdc",
    "sed -i 's/-library [^ ]* //g'  inputs/Tile_MemCore.pt.sdc",
    "python inputs/hack_sdc_unit.py inputs/global_buffer.pt.sdc",
    "sed -i 's/-library [^ ]* //g'  inputs/global_buffer.pt.sdc"
  ] )

  return g

if __name__ == '__main__':
  g = construct()
#  g.plot()
