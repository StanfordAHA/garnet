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

def construct():

  g = Graph()

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  adk_name = 'tsmc16'
  adk_view = 'stdview'

  parameters = {
    'construct_path'    : __file__,
    'design_name'       : 'pad_frame',
    'clock_period'      : 20.0,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    # Synthesis
    'flatten_effort'    : 3,
    'topographical'     : False
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl                  = Step( this_dir + '/rtl'                         )
  constraints          = Step( this_dir + '/constraints'                 )
  custom_init          = Step( this_dir + '/custom-init'                 )

  # Building whole new gdsmerge step b/c io_cells
  init_gdsmerge        = Step( this_dir + '/init-gdsmerge'               )

  # FIXME does this work? Or do we need to copy this as a whole new this_dir??
  # Like we did with init-gdsmerge above??
  print("hey ho add step so"); sys.stdout.flush()
  init_drc             = Step( this_dir + '/init-drc'                    )

  print("hey ho add step ho"); sys.stdout.flush()
  custom_power         = Step( this_dir + '/../common/custom-power-leaf' )

  # It's not plugged in yet!
  # custom_power         = Step( this_dir + '/custom-power'                )

  # Some kinda primetime thingy maybe
  # genlibdb_constraints = Step( this_dir + '/../common/custom-genlibdb-constraints' )

  # Default steps

  print("hey ho add step ho1"); sys.stdout.flush()
  info         = Step( 'info',                          default=True )
  # constraints  = Step( 'constraints',                   default=True )
  dc           = Step( 'synopsys-dc-synthesis',         default=True )
  iflow        = Step( 'cadence-innovus-flowsetup',     default=True )
  init         = Step( 'cadence-innovus-init',          default=True )
  power        = Step( 'cadence-innovus-power',         default=True )
  print("hey ho add step ho2"); sys.stdout.flush()
  place        = Step( 'cadence-innovus-place',         default=True )
  cts          = Step( 'cadence-innovus-cts',           default=True )
  postcts_hold = Step( 'cadence-innovus-postcts_hold',  default=True )
  route        = Step( 'cadence-innovus-route',         default=True )
  postroute    = Step( 'cadence-innovus-postroute',     default=True )
  signoff      = Step( 'cadence-innovus-signoff',       default=True )
  print("hey ho add step ho3"); sys.stdout.flush()
  pt_signoff   = Step( 'synopsys-pt-timing-signoff',    default=True )
  genlibdb     = Step( 'synopsys-ptpx-genlibdb',        default=True )
  gdsmerge     = Step( 'mentor-calibre-gdsmerge',       default=True )
  print("hey ho add step ho4"); sys.stdout.flush()
  drc          = Step( 'mentor-calibre-drc',            default=True )
  lvs          = Step( 'mentor-calibre-lvs',            default=True )
  debugcalibre = Step( 'cadence-innovus-debug-calibre', default=True )

  #-----------------------------------------------------------------------
  # Add extra input edges to innovus steps that need custom tweaks
  #-----------------------------------------------------------------------

  # "init" (cadence-innovus-init) inputs are "custom_init" outputs
  init.extend_inputs( custom_init.all_outputs() )

  # "power" inputs are "custom_power" outputs
  power.extend_inputs( custom_power.all_outputs() )


  # Trying a thing...
  # Want to add gds thingy to init output list
  init.extend_outputs( ["design.gds.gz"] )
  

  # genlibdb.extend_inputs( genlibdb_constraints.all_outputs() )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info                     )
  g.add_step( rtl                      )
  g.add_step( constraints              )
  g.add_step( dc                       )
  g.add_step( iflow                    )
  g.add_step( custom_init              )
  g.add_step( init                     )
  g.add_step( init_gdsmerge            )
  g.add_step( init_drc                 )
  g.add_step( power                    )
  g.add_step( custom_power             )
  g.add_step( place                    )
  g.add_step( cts                      )
  g.add_step( postcts_hold             )
  g.add_step( route                    )
  g.add_step( postroute                )
  g.add_step( signoff                  )
  g.add_step( pt_signoff   )
  # g.add_step( genlibdb_constraints     )
  g.add_step( genlibdb                 )
  g.add_step( gdsmerge                 )
  g.add_step( drc                      )
  g.add_step( lvs                      )
  g.add_step( debugcalibre             )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( adk,      dc           )
  g.connect_by_name( adk,      iflow        )
  g.connect_by_name( adk,      init         )
  g.connect_by_name( adk,      init_gdsmerge)
  g.connect_by_name( adk,      init_drc     )
  g.connect_by_name( adk,      power        )
  g.connect_by_name( adk,      place        )
  g.connect_by_name( adk,      cts          )
  g.connect_by_name( adk,      postcts_hold )
  g.connect_by_name( adk,      route        )
  g.connect_by_name( adk,      postroute    )
  g.connect_by_name( adk,      signoff      )
  g.connect_by_name( adk,      gdsmerge     )
  g.connect_by_name( adk,      drc          )
  g.connect_by_name( adk,      lvs          )

  g.connect_by_name( rtl,         dc        )
  g.connect_by_name( constraints, dc        )

  # sr02.2020 b/c now custom_init needs io_file from rtl
  g.connect_by_name( rtl,         custom_init )


  g.connect_by_name( dc,       iflow        )
  g.connect_by_name( dc,       init         )
  g.connect_by_name( dc,       power        )
  g.connect_by_name( dc,       place        )
  g.connect_by_name( dc,       cts          )

  g.connect_by_name( iflow,    init         )
  g.connect_by_name( iflow,    power        )
  g.connect_by_name( iflow,    place        )
  g.connect_by_name( iflow,    cts          )
  g.connect_by_name( iflow,    postcts_hold )
  g.connect_by_name( iflow,    route        )
  g.connect_by_name( iflow,    postroute    )
  g.connect_by_name( iflow,    signoff      )

  g.connect_by_name( custom_init,  init     )
  g.connect_by_name( custom_power, power    )

  g.connect_by_name( init,         init_gdsmerge )
  g.connect_by_name( init_gdsmerge,init_drc     )

  g.connect_by_name( init,         power        )
  g.connect_by_name( power,        place        )
  g.connect_by_name( place,        cts          )
  g.connect_by_name( cts,          postcts_hold )
  g.connect_by_name( postcts_hold, route        )
  g.connect_by_name( route,        postroute    )
  g.connect_by_name( postroute,    signoff      )
  g.connect_by_name( signoff,      gdsmerge     )
  g.connect_by_name( signoff,      drc          )
  g.connect_by_name( signoff,      lvs          )
  g.connect_by_name( gdsmerge,     drc          )
  g.connect_by_name( gdsmerge,     lvs          )

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
  # Since we are adding an additional input to the init node, we must add
  # that input to the order parameter for that node, so it actually gets run

#   init.update_params(
#     {'order': "\"main.tcl,quality-of-life.tcl,floorplan.tcl,"\
#      "add-endcaps-welltaps.tcl,make-path-groups.tcl,reporting.tcl\""}
#   )
  
  # Let's try leaving out endcaps and welltaps (and pin-assignments)
  # then maybe get clean(er) post-floorplan drc
  init.update_params(
    {'order': ['main.tcl','quality-of-life.tcl','floorplan.tcl','io_fillers.tcl']}
  )

# Not sure what this is or why it is commented out...
#   # Adding new input for genlibdb node to run 
#   genlibdb.update_params(
#                          {'order': "\"read_design.tcl genlibdb-constraints.tcl extract_model.tcl\""}
#                         )

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()


