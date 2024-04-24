#! /usr/bin/env python
# =========================================================================
# construct.py
# =========================================================================

import os

from mflowgen.components import Graph, Step
from shutil import which
from common.get_sys_adk import get_sys_adk


def construct():
    g = Graph()

    # -----------------------------------------------------------------------
    # Parameters
    # -----------------------------------------------------------------------

    adk_name = get_sys_adk()
    adk_view = 'view-standard'

    parameters = {
        'construct_path': __file__,
        'design_name': 'pad_frame',
        'clock_period': 20.0,
        'adk': adk_name,
        'adk_view': adk_view,

        # Synthesis
        'flatten_effort': 3,
        'topographical': False,

        # drc
        # drc_rule_deck: /sim/steveri/runsets/ruleset_icovl # NO GOOD instead do:
        # cd ../adks/tsmc16-adk/view-standard; ln -s /sim/steveri/runsets/ruleset_icovl
        'drc_rule_deck': 'ruleset_icovl',
    }

    # -----------------------------------------------------------------------
    # Create nodes
    # -----------------------------------------------------------------------

    this_dir = os.path.dirname(os.path.abspath(__file__))

    # ADK step
    g.set_adk(adk_name)
    adk = g.get_adk_step()

    # Custom steps
    rtl = Step(this_dir + '/rtl')
    constraints = Step(this_dir + '/constraints')
    if adk_name == 'tsmc16':
        init_fullchip = Step(this_dir + '/../common/init-fullchip-amber')
    else:
        init_fullchip = Step(this_dir + '/../common/init-fullchip')

    # Some kinda primetime thingy maybe - not using it
    # genlibdb_constraints = Step(this_dir + '/../common/custom-genlibdb-constraints')

    # Default steps
    # autopep8: off
    info         = Step('info',                          default=True)  # noqa
    # constraints= Step('constraints',                   default=True)  # noqa
    dc           = Step('synopsys-dc-synthesis',         default=True)  # noqa
    iflow        = Step('cadence-innovus-flowsetup',     default=True)  # noqa
    init         = Step('cadence-innovus-init',          default=True)  # noqa
    gdsmerge     = Step('mentor-calibre-gdsmerge',       default=True)  # noqa
    # autopep8: on

    if which("calibre") is not None:
        drc = Step('mentor-calibre-drc', default=True)
    else:
        drc = Step('cadence-pegasus-drc', default=True)

    # Send in the clones
    # "init" now builds a gds file for its own drc check "drc_icovl";
    # so need a gdsmerge step between the two
    init_gdsmerge = gdsmerge.clone()
    init_gdsmerge.set_name('init-gdsmerge')

    # icovl design-rule check runs after 'init' step
    drc_icovl = drc.clone()
    drc_icovl.set_name('drc-icovl')

    # -----------------------------------------------------------------------
    # Add extra input edges to innovus steps that need custom tweaks
    # -----------------------------------------------------------------------

    # "init" (cadence-innovus-init) inputs are "init_fullchip" outputs
    init.extend_inputs(init_fullchip.all_outputs())

    # Also: 'init' now produces a gds file
    # for intermediate drc check 'drc-icovl'
    # by way of intermediate gdsmerge step "init-gdsmerge"
    init.extend_outputs(["design.gds.gz"])

    # -----------------------------------------------------------------------
    # Graph -- Add nodes
    # -----------------------------------------------------------------------

    g.add_step(info)
    g.add_step(rtl)
    g.add_step(constraints)
    g.add_step(dc)

    g.add_step(iflow)
    g.add_step(init_fullchip)
    g.add_step(init)

    # init => init_gdsmerge => drc_icovl
    g.add_step(init_gdsmerge)
    g.add_step(drc_icovl)

    # -----------------------------------------------------------------------
    # Graph -- Add edges
    # -----------------------------------------------------------------------

    # Connect by name

    g.connect_by_name(adk, dc)
    # g.connect_by_name(adk, pre_flowsetup)
    g.connect_by_name(adk, iflow)
    g.connect_by_name(adk, init)
    g.connect_by_name(adk, init_gdsmerge)
    g.connect_by_name(adk, drc_icovl)

    g.connect_by_name(rtl, dc)
    g.connect_by_name(constraints, dc)

    # sr02.2020 b/c now init_fullchip needs io_file from rtl
    g.connect_by_name(rtl, init_fullchip)

    g.connect_by_name(dc, iflow)
    g.connect_by_name(dc, init)

    g.connect_by_name(iflow, init)
    g.connect_by_name(init_fullchip, init)

    # init => init_gdsmerge => drc_icovl
    g.connect_by_name(init, init_gdsmerge)
    g.connect_by_name(init_gdsmerge, drc_icovl)

    # -----------------------------------------------------------------------
    # Parameterize
    # -----------------------------------------------------------------------
    g.update_params(parameters)

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
            'main.tcl', 'quality-of-life.tcl',
            'stylus-compatibility-procs.tcl', 'floorplan.tcl', 'io-fillers.tcl',
            'alignment-cells.tcl',

            # Let's try it without the bump routing maybe?
            # 'gen-bumps.tcl', 'check-bumps.tcl', 'route-bumps.tcl',
            'gen-bumps.tcl',

            'sealring.tcl',
            'innovus-foundation-flow/custom-scripts/stream-out.tcl',
            'attach-results-to-outputs.tcl',
        ]}
    )
    return g


if __name__ == '__main__':
    g = construct()
