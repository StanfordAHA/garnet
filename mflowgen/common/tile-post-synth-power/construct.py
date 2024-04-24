#! /usr/bin/env python
# =========================================================================
# construct.py
# =========================================================================
# Author :
# Date   :

import os
from mflowgen.components import Graph, Step


def construct():

    g = Graph()

    # -----------------------------------------------------------------------
    # Parameters
    # -----------------------------------------------------------------------

    adk_name = 'tsmc16'
    adk_view = 'multivt'
    pwr_aware = False     # os.environ.get('PWR_AWARE')

    # autopep8: off
    parameters = {
        'construct_path'    : __file__,                              # noqa
        'design_name'       : os.environ.get('design_name'),         # noqa
        'clock_period'      : float(os.environ.get('clock_period')), # noqa
        'adk'               : adk_name,                              # noqa
        'adk_view'          : adk_view,                              # noqa
        'PWR_AWARE'         : pwr_aware,                             # noqa
        'testbench_name'    : os.environ.get('testbench_name'),      # noqa
        'strip_path'        : os.environ.get('strip_path'),          # noqa
        'waves'             : os.environ.get('waves'),               # noqa
        'use_sdf'           : os.environ.get('use_sdf'),             # noqa
        'tile_id'           : os.environ.get('tile_id')              # noqa
    }
    # autopep8: on

    # -----------------------------------------------------------------------
    # Create nodes
    # -----------------------------------------------------------------------

    # ADK step

    g.set_adk(adk_name)
    adk = g.get_adk_step()

    # Custom steps

    garnet_home = os.environ.get('GARNET_HOME')

    # autopep8: off
    setup          = Step(garnet_home + '/mflowgen/common/tile-post-synth-power/setup')  # noqa
    synth_sim      = Step(garnet_home + '/mflowgen/common/cadence-xcelium-sim'        )  # noqa
    pt_power_synth = Step(garnet_home + '/mflowgen/common/synopsys-ptpx-synth'        )  # noqa
    # autopep8: on

    synth_sim.extend_inputs(['test_vectors.txt', 'test_outputs.txt', 'design.v'])

    design = os.environ.get('design_name')
    if design == "Tile_MemCore":
        synth_sim.extend_inputs(['sram.v'])
        pt_power_synth.extend_inputs(['sram_tt.db'])

    # -----------------------------------------------------------------------
    # Graph -- Add nodes
    # -----------------------------------------------------------------------

    g.add_step(setup)
    g.add_step(synth_sim)
    g.add_step(pt_power_synth)

    # -----------------------------------------------------------------------
    # Graph -- Add edges
    # -----------------------------------------------------------------------

    g.connect_by_name(adk, synth_sim)
    g.connect_by_name(adk, pt_power_synth)
    g.connect_by_name(setup, synth_sim)
    g.connect_by_name(setup, pt_power_synth)
    g.connect_by_name(synth_sim, pt_power_synth)

    # -----------------------------------------------------------------------
    # Parameterize
    # -----------------------------------------------------------------------

    g.update_params(parameters)

    return g


if __name__ == '__main__':
    g = construct()
