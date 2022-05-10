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
  adk_view = 'view-standard'

  parameters = {
    'construct_path'    : __file__,
    'design_name'       : 'AhaGarnetSoC',
    'clock_period'      : 2.0,
    'adk'               : adk_name,
    'adk_view'          : adk_view,
    # Synthesis
    'flatten_effort'    : 3,
    'topographical'     : True,
    # RTL Generation
    'array_width'       : 32,
    'array_height'      : 16,
    'interconnect_only' : False,
    # Don't touch this parameter
    'soc_only'          : True,
    # SRAM macros
    'num_words'      : 2048,
    'word_size'      : 64,
    'mux_size'       : 8,
    'corner'         : "tt0p8v25c",
    'partial_write'  : True,
    # Low Effort flow
    'express_flow' : False,
    # TLX Ports Partitions
    'TLX_FWD_DATA_LO_WIDTH': 16,
    'TLX_REV_DATA_LO_WIDTH': 45
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
  soc_rtl        = Step( this_dir + '/../common/soc-rtl-v2'                )
  gen_sram       = Step( this_dir + '/../common/gen_sram_macro'            )
  constraints    = Step( this_dir + '/constraints'                         )
  read_design    = Step( this_dir + '/../common/fc-custom-read-design'        )
  custom_lvs     = Step( this_dir + '/custom-lvs-rules'                    )
  custom_power   = Step( this_dir + '/../common/custom-power-hierarchical' )

  # Default steps

  info         = Step( 'info',                          default=True )
  #constraints  = Step( 'constraints',                   default=True )
  dc           = Step( 'synopsys-dc-synthesis',         default=True )
  iflow        = Step( 'cadence-innovus-flowsetup',     default=True )
  init         = Step( 'cadence-innovus-init',          default=True )
  power        = Step( 'cadence-innovus-power',         default=True )
  place        = Step( 'cadence-innovus-place',         default=True )
  cts          = Step( 'cadence-innovus-cts',           default=True )
  postcts_hold = Step( 'cadence-innovus-postcts_hold',  default=True )
  route        = Step( 'cadence-innovus-route',         default=True )
  postroute    = Step( 'cadence-innovus-postroute',     default=True )
  signoff      = Step( 'cadence-innovus-signoff',       default=True )
  pt_signoff   = Step( 'synopsys-pt-timing-signoff',    default=True )
  if which("calibre") is not None:
      drc          = Step( 'mentor-calibre-drc',            default=True )
      lvs          = Step( 'mentor-calibre-lvs',            default=True )
  else:
      drc          = Step( 'cadence-pegasus-drc',           default=True )
      lvs          = Step( 'cadence-pegasus-lvs',           default=True )
  debugcalibre = Step( 'cadence-innovus-debug-calibre', default=True )

  # Add cgra tile macro inputs to downstream nodes

  dc.extend_inputs( ['sram_tt.db'] )
  pt_signoff.extend_inputs( ['sram_tt.db'] )

  # These steps need timing info for cgra tiles

  hier_steps = \
    [ iflow, init, power, place, cts, postcts_hold,
      route, postroute, signoff]

  for step in hier_steps:
    step.extend_inputs( ['sram_tt.lib', 'sram.lef'] )

  # Need the cgra tile gds's to merge into the final layout
  gdsmerge_nodes = [signoff]
  for node in gdsmerge_nodes:
      node.extend_inputs( ['sram.gds'] )

  # Need extracted spice files for both tile types to do LVS

  lvs.extend_inputs( ['sram.spi'] )

  # Add extra input edges to innovus steps that need custom tweaks

  power.extend_inputs( custom_power.all_outputs() )

  dc.extend_inputs( soc_rtl.all_outputs() )
  dc.extend_inputs( read_design.all_outputs() )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info              )
  g.add_step( rtl               )
  g.add_step( soc_rtl           )
  g.add_step( gen_sram          )
  g.add_step( constraints       )
  g.add_step( read_design       )
  g.add_step( dc                )
  g.add_step( iflow             )
  g.add_step( init              )
  g.add_step( power             )
  g.add_step( custom_power      )
  g.add_step( place             )
  g.add_step( cts               )
  g.add_step( postcts_hold      )
  g.add_step( route             )
  g.add_step( postroute         )
  g.add_step( signoff           )
  g.add_step( pt_signoff        )
  g.add_step( drc               )
  g.add_step( lvs               )
  g.add_step( custom_lvs        )
  g.add_step( debugcalibre      )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( adk,      gen_sram     )
  g.connect_by_name( adk,      dc           )
  g.connect_by_name( adk,      iflow        )
  g.connect_by_name( adk,      init         )
  g.connect_by_name( adk,      power        )
  g.connect_by_name( adk,      place        )
  g.connect_by_name( adk,      cts          )
  g.connect_by_name( adk,      postcts_hold )
  g.connect_by_name( adk,      route        )
  g.connect_by_name( adk,      postroute    )
  g.connect_by_name( adk,      signoff      )
  g.connect_by_name( adk,      drc          )
  g.connect_by_name( adk,      lvs          )

  g.connect_by_name( rtl,         dc        )
  g.connect_by_name( soc_rtl,     dc        )
  g.connect_by_name( constraints, dc        )
  g.connect_by_name( read_design, dc        )

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

  g.connect_by_name( custom_lvs,   lvs      )
  g.connect_by_name( custom_power, power    )

  # SRAM macro
  g.connect_by_name( gen_sram, dc             )
  g.connect_by_name( gen_sram, iflow          )
  g.connect_by_name( gen_sram, init           )
  g.connect_by_name( gen_sram, power          )
  g.connect_by_name( gen_sram, place          )
  g.connect_by_name( gen_sram, cts            )
  g.connect_by_name( gen_sram, postcts_hold   )
  g.connect_by_name( gen_sram, route          )
  g.connect_by_name( gen_sram, postroute      )
  g.connect_by_name( gen_sram, signoff        )
  g.connect_by_name( gen_sram, pt_signoff     )
  g.connect_by_name( gen_sram, drc            )
  g.connect_by_name( gen_sram, lvs            )

  g.connect_by_name( init,         power        )
  g.connect_by_name( power,        place        )
  g.connect_by_name( place,        cts          )
  g.connect_by_name( cts,          postcts_hold )
  g.connect_by_name( postcts_hold, route        )
  g.connect_by_name( route,        postroute    )
  g.connect_by_name( postroute,    signoff      )
  g.connect_by_name( signoff,      drc          )
  g.connect_by_name( signoff,      lvs          )
  g.connect(signoff.o('design-merged.gds'), drc.i('design_merged.gds'))
  g.connect(signoff.o('design-merged.gds'), lvs.i('design_merged.gds'))

  g.connect_by_name( adk,          pt_signoff   )
  g.connect_by_name( signoff,      pt_signoff   )

  g.connect_by_name( adk,      debugcalibre )
  g.connect_by_name( dc,       debugcalibre )
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

  # DC needs this param to set the NO_CGRA macro
  dc.update_params({'soc_only': parameters['soc_only']}, True)
  # DC needs these params to set macros in soc rtl
  dc.update_params({'TLX_FWD_DATA_LO_WIDTH' : parameters['TLX_FWD_DATA_LO_WIDTH']}, True)
  dc.update_params({'TLX_REV_DATA_LO_WIDTH' : parameters['TLX_REV_DATA_LO_WIDTH']}, True)

  init.update_params({'soc_only': parameters['soc_only']}, True)

  return g


if __name__ == '__main__':
  g = construct()
#  g.plot()
