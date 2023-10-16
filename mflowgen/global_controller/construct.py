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

  adk_name    = get_sys_adk()
  adk_view    = 'multivt'
  adk_stdcell = 'b15_7t_108pp'
  which_soc   = 'onyx-intel16'

  parameters = {
    'construct_path'    : __file__,
    'design_name'       : 'global_controller',
    'clock_period'      : 1.0*1000,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    'adk_stdcell'       : adk_stdcell,
    # Synthesis
    'flatten_effort'    : 3,
    'topographical'     : True,
    # RTL Generation
    'interconnect_only' : False,
    # Power Domains (leave this false)
    'PWR_AWARE'         : False,
    # hold target slack
    'hold_target_slack' : 0.015,
    # Utilization target
    'core_density_target' : 0.50
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl          = Step( this_dir + '/rtl'                                )
  constraints  = Step( this_dir + '/constraints'                        )
  custom_init  = Step( this_dir + '/custom-init'                        )
  custom_power = Step( this_dir + '/../common/custom-power-leaf'        )
  lib2db       = Step( this_dir + '/../common/synopsys-dc-lib2db'       )
  drc          = Step( this_dir + '/../common/intel16-synopsys-icv-drc' )
  lvs          = Step( this_dir + '/../common/intel16-synopsys-icv-lvs' )

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

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )
  
  # Add graph inputs and outputs so this can be used in hierarchical flows

  # Inputs
  g.add_input( 'design.v', rtl.i('design.v') )

  # Outputs
  g.add_output( 'global_controller_tt.lib',      genlibdb.o('design.lib')       )
  g.add_output( 'global_controller_tt.db',       genlibdb.o('design.db')        )
  g.add_output( 'global_controller.lef',         signoff.o('design.lef')        )
  g.add_output( 'global_controller.vcs.v',       signoff.o('design.vcs.v')      )
  g.add_output( 'global_controller.sdf',         signoff.o('design.sdf')        )
  g.add_output( 'global_controller.gds',         signoff.o('design-merged.gds') )
  g.add_output( 'global_controller.lvs.v',       lvs.o('design_merged.lvs.v')   )
  g.add_output( 'global_controller.vcs.pg.v',    signoff.o('design.vcs.pg.v')   )
  g.add_output( 'global_controller.spef.gz',     signoff.o('design.spef.gz')    )
  g.add_output( 'global_controller.pt.sdc',      signoff.o('design.pt.sdc')     )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info                     )
  g.add_step( rtl                      )
  g.add_step( constraints              )
  g.add_step( synth                    )
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
  g.add_step( postroute_hold           )
  g.add_step( signoff                  )
  g.add_step( pt_signoff               )
  g.add_step( genlibdb                 )
  g.add_step( lib2db                   )
  g.add_step( drc                      )
  g.add_step( lvs                      )

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

  g.connect_by_name( rtl,         synth       )
  g.connect_by_name( constraints, synth       )

  g.connect_by_name( synth,    iflow          )
  g.connect_by_name( synth,    init           )
  g.connect_by_name( synth,    power          )
  g.connect_by_name( synth,    place          )
  g.connect_by_name( synth,    cts            )

  g.connect_by_name( iflow,    init           )
  g.connect_by_name( iflow,    power          )
  g.connect_by_name( iflow,    place          )
  g.connect_by_name( iflow,    cts            )
  g.connect_by_name( iflow,    postcts_hold   )
  g.connect_by_name( iflow,    route          )
  g.connect_by_name( iflow,    postroute      )
  g.connect_by_name( iflow,    postroute_hold )
  g.connect_by_name( iflow,    signoff        )
  g.connect_by_name( iflow,    genlibdb       )
  g.connect_by_name( custom_init,  init       )
  g.connect_by_name( custom_power, power      )

  g.connect_by_name( init,           power          )
  g.connect_by_name( power,          place          )
  g.connect_by_name( place,          cts            )
  g.connect_by_name( cts,            postcts_hold   )
  g.connect_by_name( postcts_hold,   route          )
  g.connect_by_name( route,          postroute      )
  g.connect_by_name( postroute,      postroute_hold )
  g.connect_by_name( postroute_hold, signoff        )
  g.connect_by_name( signoff,        drc            )
  g.connect_by_name( signoff,        lvs            )

  g.connect_by_name( signoff,      genlibdb )
  g.connect_by_name( adk,          genlibdb )
  
  g.connect_by_name( genlibdb,     lib2db   )

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

  if which_soc == "onyx-intel16":
    new_order = [
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
      'reporting.tcl'
    ]
    init.update_params( { 'order': new_order } )
  
  # Add density target parameter
  init.update_params( { 'core_density_target': parameters['core_density_target'] }, True )

  # genlibdb -- Remove 'report-interface-timing.tcl' beacuse it takes
  # very long and is not necessary
  order = genlibdb.get_param('order')
  order.remove( 'write-interface-timing.tcl' )
  genlibdb.update_params( { 'order': order } )

  # Increase hold slack on postroute_hold step
  postroute_hold.update_params( { 'hold_target_slack': parameters['hold_target_slack'] }, allow_new=True  )

  # GLC Uses leaf-level power strategy, which is shared with other blocks
  # that use power domains flow
  power.update_params( { 'PWR_AWARE': parameters['PWR_AWARE'] }, allow_new=True  )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


