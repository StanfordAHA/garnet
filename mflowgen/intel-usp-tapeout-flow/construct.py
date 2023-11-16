#! /usr/bin/env python
#=========================================================================
# construct.py
#=========================================================================
# Author : Po-Han Chen
# Date   : 2023/10/30
#

import os
import sys

from mflowgen.components import Graph, Step, Subgraph
from common.get_sys_adk import get_sys_adk

def construct():

  g = Graph()

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  adk_name = get_sys_adk()

  parameters = {
    'construct_path'      : __file__,
    'adk'                 : adk_name,
    'adk_view'            : 'multivt',
    'adk_stdcell'         : 'b15_7t_108pp',
    'design_name'         : 'GarnetSOC_pad_frame',
    'intel_database_name' : '8su216a_tma2_0a',
    'nthreads'            : 16
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step
  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps
  node_merge_die_ring            = Step( this_dir + '/merge-die-ring' )
  node_merge_tic_before_fill     = Step( this_dir + '/merge-tic' )
  node_put_kor                   = Step( this_dir + '/put-kor' )
  node_perform_fill              = Step( this_dir + '/perform-fill' )
  node_merge_tic_after_fill      = Step( this_dir + '/merge-tic' )
  node_create_final_database     = Step( this_dir + '/create-final-database' )
  node_run_fullchip_verification = Step( this_dir + '/run-fullchip-verification' )

  #-----------------------------------------------------------------------
  # Rename duplicate nodes
  #-----------------------------------------------------------------------
  node_merge_tic_before_fill.set_name('merge-tic-before-fill')
  node_merge_tic_after_fill.set_name('merge-tic-after-fill')

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step(node_merge_die_ring)
  g.add_step(node_merge_tic_before_fill)
  g.add_step(node_put_kor)
  g.add_step(node_perform_fill)
  g.add_step(node_merge_tic_after_fill)
  g.add_step(node_create_final_database)
  g.add_step(node_run_fullchip_verification)

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( adk, node_merge_die_ring            )
  g.connect_by_name( adk, node_merge_tic_before_fill     )
  g.connect_by_name( adk, node_put_kor                   )
  g.connect_by_name( adk, node_perform_fill              )
  g.connect_by_name( adk, node_merge_tic_after_fill      )
  g.connect_by_name( adk, node_create_final_database     )
  g.connect_by_name( adk, node_run_fullchip_verification )

  g.connect_by_name( node_merge_die_ring,        node_merge_tic_before_fill     )
  # g.connect_by_name( node_merge_tic_before_fill, node_put_kor                   )
  # g.connect_by_name( node_put_kor,               node_perform_fill              )
  g.connect_by_name( node_merge_tic_before_fill, node_perform_fill              )
  g.connect_by_name( node_perform_fill,          node_merge_tic_after_fill      )
  g.connect_by_name( node_merge_tic_after_fill,  node_create_final_database     )
  g.connect_by_name( node_create_final_database, node_run_fullchip_verification )

  #-----------------------------------------------------------------------
  # Subgraph IO
  #-----------------------------------------------------------------------

  # Subgraph Inputs
  g.add_input('design.oas', node_merge_die_ring.i('design.oas'))

  # Subgraph Outputs
  g.add_output('final.oas'            , node_create_final_database.o('final.oas'))
  g.add_output('final_xor.ERRORS'     , node_run_fullchip_verification.o('final_xor.ERRORS'))
  g.add_output('final_drcd.ERRORS'    , node_run_fullchip_verification.o('final_drcd.ERRORS'))
  g.add_output('final_lu.ERRORS'      , node_run_fullchip_verification.o('final_lu.ERRORS'))
  g.add_output('final_antenna.ERRORS' , node_run_fullchip_verification.o('final_antenna.ERRORS'))
  g.add_output('final_collat.ERRORS'  , node_run_fullchip_verification.o('final_collat.ERRORS'))
  g.add_output('final_fullchip.ERRORS', node_run_fullchip_verification.o('final_fullchip.ERRORS'))

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  return g

if __name__ == '__main__':
  g = construct()
  g.plot()


