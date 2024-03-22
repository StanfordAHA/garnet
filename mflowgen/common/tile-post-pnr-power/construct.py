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

    # autopep8: off
    parameters = {
        'construct_path'    : __file__,                              # noqa
        'design_name'       : os.environ.get('design_name'),         # noqa
        'clock_period'      : float(os.environ.get('clock_period')), # noqa
        'adk'               : adk_name,                              # noqa
        'adk_view'          : adk_view,                              # noqa
        'PWR_AWARE'         : os.environ.get('PWR_AWARE'),           # noqa
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
    setup       = Step(garnet_home + '/mflowgen/common/tile-post-pnr-power/setup')  # noqa
    gl_sim      = Step(garnet_home + '/mflowgen/common/cadence-xcelium-sim'      )  # noqa
    pt_power_gl = Step(garnet_home + '/mflowgen/common/synopsys-ptpx-gl'         )  # noqa
    # autopep8: on

    gl_sim.extend_inputs(['test_vectors.txt', 'test_outputs.txt', 'design.v'])

    if os.environ.get('PWR_AWARE') == 'True':
        gl_sim.extend_inputs(["design.vcs.pg.v"])

    design = os.environ.get('design_name')
    if design == 'Tile_MemCore':
        if os.environ.get('PWR_AWARE') == 'True':
            gl_sim.extend_inputs(['sram-pwr.v'])
        else:
            gl_sim.extend_inputs(['sram.v'])
        pt_power_gl.extend_inputs(['sram_tt.db'])

    # -----------------------------------------------------------------------
    # Graph -- Add nodes
    # -----------------------------------------------------------------------

    g.add_step(setup)
    g.add_step(gl_sim)
    g.add_step(pt_power_gl)

    # -----------------------------------------------------------------------
    # Graph -- Add edges
    # -----------------------------------------------------------------------

    g.connect_by_name(adk, gl_sim)
    g.connect_by_name(adk, pt_power_gl)
    g.connect_by_name(setup, gl_sim)
    g.connect_by_name(setup, pt_power_gl)
    g.connect_by_name(gl_sim, pt_power_gl)

    # -----------------------------------------------------------------------
    # Parameterize
    # -----------------------------------------------------------------------

    g.update_params(parameters)

    return g


if __name__ == '__main__':
    g = construct()
