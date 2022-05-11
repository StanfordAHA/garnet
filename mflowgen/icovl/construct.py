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
    'design_name'       : 'pad_frame',
    'clock_period'      : 20.0,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    #
    # Synthesis
    'flatten_effort'    : 3,
    'topographical'     : False,
    #
    # drc
    # drc_rule_deck: /sim/steveri/runsets/ruleset_icovl # NO GOOD instead do:
    # cd ../adks/tsmc16-adk/view-standard; ln -s /sim/steveri/runsets/ruleset_icovl
    'drc_rule_deck'     : 'ruleset_icovl',
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step
  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps
  rtl                  = Step( this_dir + '/rtl'                   )
  constraints          = Step( this_dir + '/constraints'           )
  init_fullchip        = Step( this_dir + '/../common/init-fullchip')

#   # More custom steps: custom power step (unused)
#   custom_power         = Step( this_dir + '/../common/custom-power-leaf' )

  # Some kinda primetime thingy maybe - not using it
  # genlibdb_constraints = Step( this_dir + '/../common/custom-genlibdb-constraints' )

  # Default steps
  info         = Step( 'info',                          default=True )
  # constraints= Step( 'constraints',                   default=True )
  dc           = Step( 'synopsys-dc-synthesis',         default=True )
  iflow        = Step( 'cadence-innovus-flowsetup',     default=True )
  init         = Step( 'cadence-innovus-init',          default=True )

#   power        = Step( 'cadence-innovus-power',         default=True )
#   place        = Step( 'cadence-innovus-place',         default=True )
#   cts          = Step( 'cadence-innovus-cts',           default=True )
#   postcts_hold = Step( 'cadence-innovus-postcts_hold',  default=True )
#   route        = Step( 'cadence-innovus-route',         default=True )
#   postroute    = Step( 'cadence-innovus-postroute',     default=True )
#   signoff      = Step( 'cadence-innovus-signoff',       default=True )
#   pt_signoff   = Step( 'synopsys-pt-timing-signoff',    default=True )
#   genlibdb     = Step( 'synopsys-ptpx-genlibdb',        default=True )
  gdsmerge     = Step( 'mentor-calibre-gdsmerge',       default=True )
  if which("calibre") is not None:
      drc          = Step( 'mentor-calibre-drc',            default=True )
  else:
      drc          = Step( 'cadence-pegasus-drc',           default=True )
#   lvs          = Step( 'mentor-calibre-lvs',            default=True )
#   debugcalibre = Step( 'cadence-innovus-debug-calibre', default=True )

  # Send in the clones
  # "init" now builds a gds file for its own drc check "drc_icovl";
  # so need a gdsmerge step between the two
  init_gdsmerge = gdsmerge.clone()
  init_gdsmerge.set_name( 'init-gdsmerge' )

  # icovl design-rule check runs after 'init' step
  drc_icovl = drc.clone()
  drc_icovl.set_name( 'drc-icovl' )


  #-----------------------------------------------------------------------
  # Add extra input edges to innovus steps that need custom tweaks
  #-----------------------------------------------------------------------

  # "init" (cadence-innovus-init) inputs are "init_fullchip" outputs
  init.extend_inputs( init_fullchip.all_outputs() )

  # Also: 'init' now produces a gds file
  # for intermediate drc check 'drc-icovl'
  # by way of intermediate gdsmerge step "init-gdsmerge"
  init.extend_outputs( ["design.gds.gz"] )
  
#   # "power" inputs are "custom_power" outputs
#   power.extend_inputs( custom_power.all_outputs() )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info                     )
  g.add_step( rtl                      )
  g.add_step( constraints              )
  g.add_step( dc                       )

  # pre_flowsetup => iflow
#   g.add_step( pre_flowsetup            )


  g.add_step( iflow                    )
  g.add_step( init_fullchip            )
  g.add_step( init                     )

  # init => init_gdsmerge => drc_icovl
  g.add_step( init_gdsmerge            )
  g.add_step( drc_icovl                 )

#   g.add_step( power                    )
#   g.add_step( custom_power             )
#   g.add_step( place                    )
#   g.add_step( cts                      )
#   g.add_step( postcts_hold             )
#   g.add_step( route                    )
#   g.add_step( postroute                )
#   g.add_step( signoff                  )
#   g.add_step( pt_signoff   )
#   # g.add_step( genlibdb_constraints     )
#   g.add_step( genlibdb                 )
#   g.add_step( gdsmerge                 )
#   g.add_step( drc                      )
#   g.add_step( lvs                      )
#   g.add_step( debugcalibre             )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( adk,      dc           )
#   g.connect_by_name( adk,      pre_flowsetup )
  g.connect_by_name( adk,      iflow        )
  g.connect_by_name( adk,      init         )
  g.connect_by_name( adk,      init_gdsmerge)
  g.connect_by_name( adk,      drc_icovl     )

#   g.connect_by_name( adk,      power        )
#   g.connect_by_name( adk,      place        )
#   g.connect_by_name( adk,      cts          )
#   g.connect_by_name( adk,      postcts_hold )
#   g.connect_by_name( adk,      route        )
#   g.connect_by_name( adk,      postroute    )
#   g.connect_by_name( adk,      signoff      )
#   g.connect_by_name( adk,      gdsmerge     )
#   g.connect_by_name( adk,      drc          )
#   g.connect_by_name( adk,      lvs          )

  g.connect_by_name( rtl,         dc        )
  g.connect_by_name( constraints, dc        )

  # sr02.2020 b/c now init_fullchip needs io_file from rtl
  g.connect_by_name( rtl,      init_fullchip)

  g.connect_by_name( dc,       iflow        )
  g.connect_by_name( dc,       init         )

#   g.connect_by_name( dc,       power        )
#   g.connect_by_name( dc,       place        )
#   g.connect_by_name( dc,       cts          )


# Maybe don't need this no more...
#   # g.connect_by_name( pre_flowsetup,  iflow   )
#   # iflow, init, power, place, cts, postcts_hold, route, postroute, signoff
#   for step in pre_flowsetup_followers:
#     g.connect_by_name( pre_flowsetup, step)


  g.connect_by_name( iflow,    init         )

#   g.connect_by_name( iflow,    power        )
#   g.connect_by_name( iflow,    place        )
#   g.connect_by_name( iflow,    cts          )
#   g.connect_by_name( iflow,    postcts_hold )
#   g.connect_by_name( iflow,    route        )
#   g.connect_by_name( iflow,    postroute    )
#   g.connect_by_name( iflow,    signoff      )
#   # for step in iflow_followers:
#   #   g.connect_by_name( iflow, step)

  g.connect_by_name( init_fullchip, init   )

#   g.connect_by_name( custom_power,  power  )

  # init => init_gdsmerge => drc_icovl
  g.connect_by_name( init,         init_gdsmerge )
  g.connect_by_name( init_gdsmerge,drc_icovl     )

#   g.connect_by_name( init,         power        )
#   g.connect_by_name( power,        place        )
#   g.connect_by_name( place,        cts          )
#   g.connect_by_name( cts,          postcts_hold )
#   g.connect_by_name( postcts_hold, route        )
#   g.connect_by_name( route,        postroute    )
#   g.connect_by_name( postroute,    signoff      )
#   g.connect_by_name( signoff,      gdsmerge     )
#   g.connect_by_name( signoff,      drc          )
#   g.connect_by_name( signoff,      lvs          )
#   g.connect_by_name( gdsmerge,     drc          )
#   g.connect_by_name( gdsmerge,     lvs          )

#   g.connect_by_name( signoff,              genlibdb )
#   g.connect_by_name( adk,                  genlibdb )
# #   g.connect_by_name( genlibdb_constraints, genlibdb )

#   g.connect_by_name( adk,          pt_signoff   )
#   g.connect_by_name( signoff,      pt_signoff   )
# 
#   g.connect_by_name( adk,      debugcalibre )
#   g.connect_by_name( dc,       debugcalibre )
#   g.connect_by_name( iflow,    debugcalibre )
#   g.connect_by_name( signoff,  debugcalibre )
#   g.connect_by_name( drc,      debugcalibre )
#   g.connect_by_name( lvs,      debugcalibre )

  # yes? no?
  # g.connect_by_name( drc_icovl,      debugcalibre )

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
  # 3/4 swapped order of streamout/align so to get gds *before* icovl


  init.update_params(
    {'order': [
      'main.tcl','quality-of-life.tcl',
      'stylus-compatibility-procs.tcl','floorplan.tcl','io-fillers.tcl',
      'alignment-cells.tcl',

      # Let's try it without the bump routing maybe?
      # 'gen-bumps.tcl', 'check-bumps.tcl', 'route-bumps.tcl',
      'gen-bumps.tcl',

      'sealring.tcl',
      'innovus-foundation-flow/custom-scripts/stream-out.tcl',
      'attach-results-to-outputs.tcl',
    ]}
  )

  # Not sure what this is or why it was commented out...
  #   # Adding new input for genlibdb node to run 
  #   genlibdb.update_params(
  #     {'order': "\"read_design.tcl genlibdb-constraints.tcl extract_model.tcl\""}
  #   )

  return g


if __name__ == '__main__':
  g = construct()
  # g.plot()
