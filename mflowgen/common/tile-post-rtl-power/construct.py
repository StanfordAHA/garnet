#! /usr/bin/env python
# =========================================================================
# construct.py  --  tile-post-rtl-power sub-graph
# =========================================================================
# RTL-activity power: simulate the tile's RTL (design.v) with the app's
# per-tile stimulus to get an RTL-name SAIF, then compute power on the
# signed-off gate netlist via synopsys-ptpx-rtl, which `source`s the Genus
# design.namemap to bind the RTL SAIF onto the gate netlist.
#
# Mirrors tile-post-pnr-power (which sims the routed netlist -> ptpx-gl),
# swapping the gate-level sim for an RTL sim and ptpx-gl for ptpx-rtl.

import os
from mflowgen.components import Graph, Step


def construct():

    g = Graph()

    # -----------------------------------------------------------------------
    # Parameters
    # -----------------------------------------------------------------------

    adk_name = 'tsmc16'
    adk_view = 'multivt'

    if adk_name == 'gf12-adk':
        adk_view = 'view-standard'

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

    g.set_adk(adk_name)
    adk = g.get_adk_step()

    garnet_home = os.environ.get('GARNET_HOME')

    # autopep8: off
    setup        = Step(garnet_home + '/mflowgen/common/tile-post-rtl-power/setup')  # noqa
    rtl_sim      = Step(garnet_home + '/mflowgen/common/cadence-xcelium-sim'       )  # noqa
    pt_power_rtl = Step(garnet_home + '/mflowgen/common/synopsys-ptpx-rtl'         )  # noqa
    # autopep8: on

    # The sim runs the RTL design.v (behavioral), NOT the routed netlist, so it
    # produces an RTL-name SAIF. No SDF back-annotation (RTL has no delays).
    rtl_sim.extend_inputs(['test_vectors.txt', 'test_outputs.txt', 'design.v'])

    design = os.environ.get('design_name')
    if design == 'Tile_MemCore':
        # Behavioral SRAM for the RTL sim; the SRAM .db for the power calc.
        rtl_sim.extend_inputs(['sram.v'])
        pt_power_rtl.extend_inputs(['sram_tt.db'])

    # -----------------------------------------------------------------------
    # Graph -- Add nodes
    # -----------------------------------------------------------------------

    g.add_step(setup)
    g.add_step(rtl_sim)
    g.add_step(pt_power_rtl)

    # -----------------------------------------------------------------------
    # Graph -- Add edges
    # -----------------------------------------------------------------------

    g.connect_by_name(adk, rtl_sim)
    g.connect_by_name(adk, pt_power_rtl)
    g.connect_by_name(setup, rtl_sim)      # design.v (RTL) + test vectors
    g.connect_by_name(setup, pt_power_rtl) # design.vcs.v + spef + sdc + namemap
    g.connect_by_name(rtl_sim, pt_power_rtl)  # run.saif

    # -----------------------------------------------------------------------
    # Parameterize
    # -----------------------------------------------------------------------

    g.update_params(parameters)

    return g


if __name__ == '__main__':
    g = construct()
