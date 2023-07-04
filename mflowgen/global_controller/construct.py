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
  which_soc = 'onyx'

  # TSMC override(s)
  if adk_name == 'tsmc16':
    adk_view = 'multicorner'
    which_soc = 'amber'

  parameters = {
    'construct_path'    : __file__,
    'design_name'       : 'global_controller',
    'clock_period'      : 1.0,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
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
    'core_density_target' : 0.50,
    'drc_env_setup'     : 'drcenv-block.sh'
  }

  # TSMC overrides
  if adk_name == 'tsmc16': parameters.update({
    'hold_target_slack' : 0.030,
  })

  # OG TSMC did not specify drc_env_setup
  if adk_name == 'tsmc16':
    parameters.pop('drc_env_setup')

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl                  = Step( this_dir + '/rtl'                                   )
  constraints          = Step( this_dir + '/constraints'                           )
  custom_init          = Step( this_dir + '/custom-init'                           )
  if adk_name == 'tsmc16':
    custom_power         = Step( this_dir + '/../common/custom-power-leaf-amber'      )
  else:
    custom_power         = Step( this_dir + '/../common/custom-power-leaf'            )
  lib2db               = Step( this_dir + '/../common/synopsys-dc-lib2db'          )
  lib2db               = Step( this_dir + '/../common/synopsys-dc-lib2db'          )
  if which_soc == "onyx":
    drc_pm               = Step( this_dir + '/../common/gf-mentor-calibre-drcplus-pm')
    drc_mas              = Step( this_dir + '/../common/gf-mentor-calibre-drc-mas'   )


  # Default steps

  info         = Step( 'info',                          default=True )
  #constraints  = Step( 'constraints',                   default=True )
  synth        = Step( 'cadence-genus-synthesis',       default=True )
  iflow        = Step( 'cadence-innovus-flowsetup',     default=True )
  init         = Step( 'cadence-innovus-init',          default=True )
  power        = Step( 'cadence-innovus-power',         default=True )
  place        = Step( 'cadence-innovus-place',         default=True )
  cts          = Step( 'cadence-innovus-cts',           default=True )
  postcts_hold = Step( 'cadence-innovus-postcts_hold',  default=True )
  route        = Step( 'cadence-innovus-route',         default=True )
  postroute    = Step( 'cadence-innovus-postroute',     default=True )
  postroute_hold    = Step( 'cadence-innovus-postroute_hold',default=True )
  signoff      = Step( 'cadence-innovus-signoff',       default=True )
  pt_signoff   = Step( 'synopsys-pt-timing-signoff',    default=True )
  genlib       = Step( 'cadence-innovus-genlib',        default=True )
  if which("calibre") is not None:
      drc          = Step( 'mentor-calibre-drc',            default=True )
      lvs          = Step( 'mentor-calibre-lvs',            default=True )
  else:
      drc          = Step( 'cadence-pegasus-drc',           default=True )
      lvs          = Step( 'cadence-pegasus-lvs',           default=True )
  debugcalibre = Step( 'cadence-innovus-debug-calibre', default=True )

  # Add extra input edges to innovus steps that need custom tweaks

  init.extend_inputs( custom_init.all_outputs() )
  power.extend_inputs( custom_power.all_outputs() )

  # Must adjust pin_cap_tolerance to prevent this:
  # **ERROR: (TECHLIB-1071): Identified pin capacitance mismatch
  #   '0.015400' and '0.015300' in pin 'trst_n', for cell
  #   'global_controller', between libraries 'analysis_default.lib' and
  #   'analysis_hold.lib'. The libraries cannot be used for merging.

  cmd = "cat scripts/extract_model.tcl | sed 's/\(merge_model_timing.*\)/\\1 -pin_cap_tolerance .001/' > inputs/extract_model.tcl"
  genlib.pre_extend_commands( [ cmd ] )

  # TSMC needs streamout *without* the (new) default -uniquify flag
  # This python script finds 'stream-out.tcl' and strips out that flag.
  if adk_name == "tsmc16":
    from common.streamout_no_uniquify import streamout_no_uniquify
    streamout_no_uniquify(iflow)

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
  g.add_step( postroute_hold )
  g.add_step( signoff                  )
  g.add_step( pt_signoff   )
  g.add_step( genlib                   )
  g.add_step( lib2db                   )
  g.add_step( drc                      )
  if which_soc == "onyx":
    g.add_step( drc_pm                   )
    g.add_step( drc_mas                  )
  g.add_step( lvs                      )
  g.add_step( debugcalibre             )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( adk,      synth           )
  g.connect_by_name( adk,      iflow        )
  g.connect_by_name( adk,      init         )
  g.connect_by_name( adk,      power        )
  g.connect_by_name( adk,      place        )
  g.connect_by_name( adk,      cts          )
  g.connect_by_name( adk,      postcts_hold )
  g.connect_by_name( adk,      route        )
  g.connect_by_name( adk,      postroute    )
  g.connect_by_name( adk,      postroute_hold )
  g.connect_by_name( adk,      signoff      )
  g.connect_by_name( adk,      drc          )
  if which_soc == "onyx":
    g.connect_by_name( adk,      drc_pm       )
    g.connect_by_name( adk,      drc_mas      )
  g.connect_by_name( adk,      lvs          )

  g.connect_by_name( rtl,         synth     )
  g.connect_by_name( constraints, synth     )

  g.connect_by_name( synth,    iflow        )
  g.connect_by_name( synth,    init         )
  g.connect_by_name( synth,    power        )
  g.connect_by_name( synth,    place        )
  g.connect_by_name( synth,    cts          )

  g.connect_by_name( iflow,    init           )
  g.connect_by_name( iflow,    power          )
  g.connect_by_name( iflow,    place          )
  g.connect_by_name( iflow,    cts            )
  g.connect_by_name( iflow,    postcts_hold   )
  g.connect_by_name( iflow,    route          )
  g.connect_by_name( iflow,    postroute      )
  g.connect_by_name( iflow,    postroute_hold )
  g.connect_by_name( iflow,    signoff        )
  g.connect_by_name( iflow,    genlib         )

  g.connect_by_name( custom_init,  init     )
  g.connect_by_name( custom_power, power    )

  g.connect_by_name( init,         power        )
  g.connect_by_name( power,        place        )
  g.connect_by_name( place,        cts          )
  g.connect_by_name( cts,          postcts_hold )
  g.connect_by_name( postcts_hold, route        )
  g.connect_by_name( route,        postroute    )
  g.connect_by_name( postroute,      postroute_hold )
  g.connect_by_name( postroute_hold, signoff        )
  g.connect_by_name( signoff,      drc          )
  if which_soc == "onyx":
    g.connect_by_name( signoff,      drc_pm       )
    g.connect_by_name( signoff,      drc_mas       )
  g.connect_by_name( signoff,      lvs          )
  g.connect(signoff.o('design-merged.gds'), drc.i('design_merged.gds'))
  if which_soc == "onyx":
    g.connect(signoff.o('design-merged.gds'), drc_pm.i('design_merged.gds'))
    g.connect(signoff.o('design-merged.gds'), drc_mas.i('design_merged.gds'))
  g.connect(signoff.o('design-merged.gds'), lvs.i('design_merged.gds'))

  g.connect_by_name( signoff,      genlib   )
  g.connect_by_name( adk,          genlib   )
  
  g.connect_by_name( genlib,       lib2db   )

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( synth,    debugcalibre )
  g.connect_by_name( iflow,    debugcalibre )
  g.connect_by_name( signoff,  debugcalibre )
  g.connect_by_name( drc,      debugcalibre )
  if which_soc == "onyx":
    g.connect_by_name( drc_pm,   debugcalibre )
  g.connect_by_name( lvs,      debugcalibre )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  # Since we are adding an additional input script to the generic Innovus
  # steps, we modify the order parameter for that node which determines
  # which scripts get run and when they get run.

  if which_soc == "amber":
    # init -- Add 'add-endcaps-welltaps.tcl' after 'floorplan.tcl'

    order = init.get_param('order') # get the default script run order
    floorplan_idx = order.index( 'floorplan.tcl' ) # find floorplan.tcl
    order.insert( floorplan_idx + 1, 'add-endcaps-welltaps.tcl' ) # add here
    init.update_params( { 'order': order } )
  
  # Add density target parameter
  init.update_params( { 'core_density_target': parameters['core_density_target'] }, True )

  # Increase hold slack on postroute_hold step
  postroute_hold.update_params( { 'hold_target_slack': parameters['hold_target_slack'] }, allow_new=True  )

  # GLC Uses leaf-level power strategy, which is shared with other blocks
  # that use power domains flow
  power.update_params( { 'PWR_AWARE': parameters['PWR_AWARE'] }, allow_new=True  )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


