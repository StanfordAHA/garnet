#! /usr/bin/env python
# =========================================================================
# construct.py
# =========================================================================
# Author :
# Date   :

import os
from mflowgen.components import Graph, Step
from shutil import which
from common.get_sys_adk import get_sys_adk


def construct():

    g = Graph()

    # -----------------------------------------------------------------------
    # Parameters
    # -----------------------------------------------------------------------

    adk_name = get_sys_adk()  # E.g. 'gf12-adk' or 'tsmc16'
    adk_view = 'multivt'
    pwr_aware = True

    if pwr_aware:
        adk_view = adk_view + '-pm'

    flatten = 3
    if os.environ.get('FLATTEN'):
        flatten = os.environ.get('FLATTEN')

    synth_power = False
    if os.environ.get('SYNTH_POWER') == 'True':
        synth_power = True
    # power domains do not work with post-synth power
    if synth_power:
        pwr_aware = False

    want_drc_pm = True
    want_custom_cts = True

    # TSMC override(s)
    if adk_name == 'tsmc16':
        adk_view = 'multicorner-multivt'
        want_drc_pm = False
        want_custom_cts = False

    if adk_name == 'tsmc16':
        read_hdl_defines = 'TSMC16'
    elif adk_name == 'gf12-adk':
        read_hdl_defines = 'GF12'
    else:
        read_hdl_defines = ''

    parameters = {
        'construct_path': __file__,
        'design_name': 'Tile_PE',
        'clock_period': 1.1,
        'adk': adk_name,
        'adk_view': adk_view,

        # Synthesis
        'flatten_effort': flatten,
        'topographical': True,
        'read_hdl_defines': read_hdl_defines,

        # RTL Generation
        'interconnect_only': False,
        'rtl_docker_image': 'default',  # Current default is 'stanfordaha/garnet:latest'

        # Power Domains
        'PWR_AWARE': pwr_aware,
        'core_density_target': 0.6,

        # Power analysis
        "use_sdf": False,  # uses sdf but not the way it is in xrun node
        'app_to_run': 'tests/conv_3_3',
        'saif_instance': 'testbench/dut',
        'testbench_name': 'testbench',
        'strip_path': 'testbench/dut',
        'drc_env_setup': 'drcenv-block.sh'
    }
    # TSMC overrides
    if adk_name == 'tsmc16':
        parameters.update({
            'interconnect_only': True,
            'core_density_target': 0.63,
        })

    # User-level option to change clock frequency
    # E.g. 'export clock_period_PE="4.0"' to target 250MHz
    # Optionally could restrict to bk only: if (os.getenv('USER') == "buildkite-agent")
    cp = os.getenv('clock_period_PE')
    if (cp != None):
        print("@file_info: WARNING found env var 'clock_period_PE'")
        print("@file_info: WARNING setting PE clock period to '%s'" % cp)
        parameters['clock_period'] = cp

    # -----------------------------------------------------------------------
    # Create nodes
    # -----------------------------------------------------------------------

    this_dir = os.path.dirname(os.path.abspath(__file__))

    # ADK step

    g.set_adk(adk_name)
    adk = g.get_adk_step()

    # Custom steps
    def custom_step(path):
        return Step(this_dir + path)

    rtl = custom_step('/../common/rtl')
    constraints = custom_step('/constraints')
    custom_init = custom_step('/custom-init')
    custom_genus_scripts = custom_step('/custom-genus-scripts')
    custom_flowgen_setup = custom_step('/custom-flowgen-setup')
    if adk_name == 'tsmc16':
        custom_power = custom_step('/../common/custom-power-leaf-amber')
    else:
        custom_power = custom_step('/../common/custom-power-leaf')
    if want_custom_cts:
        custom_cts = custom_step('/custom-cts')
    short_fix = custom_step('/../common/custom-short-fix')
    genlibdb_constraints = custom_step('/../common/custom-genlibdb-constraints')
    custom_timing_assert = custom_step('/../common/custom-timing-assert')
    custom_dc_scripts = custom_step('/custom-dc-scripts')
    testbench = custom_step('/../common/testbench')
    application = custom_step('/../common/application')
    lib2db = custom_step('/../common/synopsys-dc-lib2db')
    if want_drc_pm:
        drc_pm = custom_step('/../common/gf-mentor-calibre-drcplus-pm')
    if synth_power:
        post_synth_power = custom_step('/../common/tile-post-synth-power')
    post_pnr_power = custom_step('/../common/tile-post-pnr-power')

    # Power aware setup
    power_domains = None
    pwr_aware_gls = None
    if pwr_aware:
        power_domains = custom_step('/../common/power-domains')
        pwr_aware_gls = custom_step('/../common/pwr-aware-gls')

    # Default steps - turn off formatting b/c want these columns to line up
    # autopep8: off
    info         = Step('info',                          default=True)  # noqa
    synth        = Step('cadence-genus-synthesis',       default=True)  # noqa
    iflow        = Step('cadence-innovus-flowsetup',     default=True)  # noqa
    init         = Step('cadence-innovus-init',          default=True)  # noqa
    power        = Step('cadence-innovus-power',         default=True)  # noqa
    place        = Step('cadence-innovus-place',         default=True)  # noqa
    cts          = Step('cadence-innovus-cts',           default=True)  # noqa
    postcts_hold = Step('cadence-innovus-postcts_hold',  default=True)  # noqa
    route        = Step('cadence-innovus-route',         default=True)  # noqa
    postroute    = Step('cadence-innovus-postroute',     default=True)  # noqa
    signoff      = Step('cadence-innovus-signoff',       default=True)  # noqa
    pt_signoff   = Step('synopsys-pt-timing-signoff',    default=True)  # noqa
    genlibdb     = Step('synopsys-ptpx-genlibdb',        default=True)  # noqa
    # autopep8: on

    if which("calibre") is not None:
        drc = Step('mentor-calibre-drc', default=True)
        lvs = Step('mentor-calibre-lvs', default=True)
    else:
        drc = Step('cadence-pegasus-drc', default=True)
        lvs = Step('cadence-pegasus-lvs', default=True)
    debugcalibre = Step('cadence-innovus-debug-calibre', default=True)

    # Add custom timing scripts
    custom_timing_steps = [synth, postcts_hold, signoff]  # connects to these
    for c_step in custom_timing_steps:
        c_step.extend_inputs(custom_timing_assert.all_outputs())

    # Add extra input edges to innovus steps that need custom tweaks
    init.extend_inputs(custom_init.all_outputs())
    power.extend_inputs(custom_power.all_outputs())
    genlibdb.extend_inputs(genlibdb_constraints.all_outputs())
    synth.extend_inputs(custom_genus_scripts.all_outputs())
    iflow.extend_inputs(custom_flowgen_setup.all_outputs())

    # Extra input to DC for constraints
    synth.extend_inputs([
        "common.tcl", "reporting.tcl", "generate-results.tcl",
        "scenarios.tcl", "report_alu.py", "parse_alu.py"])

    # Extra outputs from DC
    synth.extend_outputs(["sdc"])
    iflow.extend_inputs(["scenarios.tcl", "sdc"])
    init.extend_inputs(["sdc"])
    power.extend_inputs(["sdc"])
    place.extend_inputs(["sdc"])
    cts.extend_inputs(["sdc"])

    order = synth.get_param('order')
    order.append('copy_sdc.tcl')
    synth.set_param('order', order)

    # Power aware setup
    if pwr_aware:

        # Need pe-pd-params so adk.tcl can access parm 'adk_allow_sdf_regs'
        # (pe-pd-params come from already-connected 'power-domains' node)
        synth.extend_inputs(['pe-pd-params.tcl',
                             'designer-interface.tcl',
                             'upf_Tile_PE.tcl',
                             'pe-constraints.tcl',
                             'pe-constraints-2.tcl',
                             'dc-dont-use-constraints.tcl'])

        # Eventually want to extend this to GF as well...!
        if adk_name == 'tsmc16':
            synth.extend_inputs(['check-pdcr-address.sh'])

        init.extend_inputs(['upf_Tile_PE.tcl',
                            'pe-load-upf.tcl',
                            'dont-touch-constraints.tcl',
                            'pe-pd-params.tcl',
                            'pd-aon-floorplan.tcl',
                            'add-endcaps-welltaps-setup.tcl',
                            'pd-add-endcaps-welltaps.tcl',
                            'add-power-switches.tcl',
                            'check-clamp-logic-structure.tcl'])

        # Eventually want to extend this to GF as well...!
        if adk_name == 'tsmc16':
            init.extend_inputs(['check-pdcr-address.sh'])

        # Need pe-pd-params for parm 'vdd_m3_stripe_sparsity'
        # pd-globalnetconnect, pe-pd-params come from 'power-domains' node
        power.extend_inputs(['pd-globalnetconnect.tcl', 'pe-pd-params.tcl'])

        place.extend_inputs(['place-dont-use-constraints.tcl',
                             'check-clamp-logic-structure.tcl',
                             'add-aon-tie-cells.tcl'])
        cts.extend_inputs(['conn-aon-cells-vdd.tcl', 'check-clamp-logic-structure.tcl'])
        postcts_hold.extend_inputs(['conn-aon-cells-vdd.tcl', 'check-clamp-logic-structure.tcl'])
        route.extend_inputs(['conn-aon-cells-vdd.tcl', 'check-clamp-logic-structure.tcl'])
        postroute.extend_inputs(['conn-aon-cells-vdd.tcl', 'check-clamp-logic-structure.tcl'])
        signoff.extend_inputs(['conn-aon-cells-vdd.tcl',
                               'pd-generate-lvs-netlist.tcl',
                               'check-clamp-logic-structure.tcl'])
        pwr_aware_gls.extend_inputs(['design.vcs.pg.v'])

        # Eventually want to extend this to GF as well...!
        if adk_name == 'tsmc16':
            # Fix and repair PowerDomainConfigReg when/if magma decides to renumber it :(
            synth.pre_extend_commands(['./inputs/check-pdcr-address.sh'])
            init.pre_extend_commands(['./inputs/check-pdcr-address.sh'])
            pwr_aware_gls.pre_extend_commands(['./assign-pdcr-address.sh'])

    # Add short_fix script(s) to list of available postroute scripts
    postroute.extend_inputs(short_fix.all_outputs())

    # Add graph inputs and outputs so this can be used in hierarchical flows

    # Inputs
    g.add_input('design.v', rtl.i('design.v'))

    # Outputs - turn off formatting b/c want these columns to line up
    # autopep8: off
    g.add_output('Tile_PE_tt.lib',      genlibdb.o('design.lib')       )  # noqa
    g.add_output('Tile_PE_tt.db',       genlibdb.o('design.db')        )  # noqa
    g.add_output('Tile_PE.lef',         signoff.o('design.lef')        )  # noqa
    g.add_output('Tile_PE.gds',         signoff.o('design-merged.gds') )  # noqa
    g.add_output('Tile_PE.sdf',         signoff.o('design.sdf')        )  # noqa
    g.add_output('Tile_PE.vcs.v',       signoff.o('design.vcs.v')      )  # noqa
    g.add_output('Tile_PE.vcs.pg.v',    signoff.o('design.vcs.pg.v')   )  # noqa
    g.add_output('Tile_PE.spef.gz',     signoff.o('design.spef.gz')    )  # noqa
    g.add_output('Tile_PE.pt.sdc',      signoff.o('design.pt.sdc')     )  # noqa
    g.add_output('Tile_PE.lvs.v',       lvs.o('design_merged.lvs.v')   )  # noqa
    # autopep8: on

    # TSMC needs streamout *without* the (new) default -uniquify flag
    # This python method finds 'stream-out.tcl' and strips out that flag.
    from common.streamout_no_uniquify import streamout_no_uniquify
    if adk_name == "tsmc16":
        streamout_no_uniquify(iflow)

    # -----------------------------------------------------------------------
    # Graph -- Add nodes
    # -----------------------------------------------------------------------

    g.add_step(info)
    g.add_step(rtl)
    g.add_step(constraints)
    g.add_step(custom_dc_scripts)
    g.add_step(synth)
    g.add_step(custom_timing_assert)
    g.add_step(custom_genus_scripts)
    g.add_step(iflow)
    g.add_step(custom_flowgen_setup)
    g.add_step(init)
    g.add_step(custom_init)
    g.add_step(power)
    g.add_step(custom_power)
    g.add_step(place)
    g.add_step(cts)
    g.add_step(postcts_hold)
    g.add_step(route)
    g.add_step(postroute)
    g.add_step(short_fix)
    g.add_step(signoff)
    g.add_step(pt_signoff)
    g.add_step(genlibdb_constraints)
    g.add_step(genlibdb)
    g.add_step(lib2db)
    g.add_step(drc)
    g.add_step(lvs)
    g.add_step(debugcalibre)

    g.add_step(application)
    g.add_step(testbench)
    if synth_power:
        g.add_step(post_synth_power)
    g.add_step(post_pnr_power)

    # Power aware step
    if pwr_aware:
        g.add_step(power_domains)
        g.add_step(pwr_aware_gls)

    # -----------------------------------------------------------------------
    # Graph -- Add edges
    # -----------------------------------------------------------------------

    # Dynamically add edges

    # Connect by name

    g.connect_by_name(adk, synth)
    g.connect_by_name(adk, iflow)
    g.connect_by_name(adk, init)
    g.connect_by_name(adk, power)
    g.connect_by_name(adk, place)
    g.connect_by_name(adk, cts)
    g.connect_by_name(adk, postcts_hold)
    g.connect_by_name(adk, route)
    g.connect_by_name(adk, postroute)
    g.connect_by_name(adk, signoff)
    g.connect_by_name(adk, drc)
    g.connect_by_name(adk, lvs)

    g.connect_by_name(rtl, synth)
    g.connect_by_name(constraints, synth)
    g.connect_by_name(custom_genus_scripts, synth)
    g.connect_by_name(constraints, iflow)
    g.connect_by_name(custom_dc_scripts, iflow)

    for c_step in custom_timing_steps:
        g.connect_by_name(custom_timing_assert, c_step)

    g.connect_by_name(synth, iflow)
    g.connect_by_name(synth, init)
    g.connect_by_name(synth, power)
    g.connect_by_name(synth, place)
    g.connect_by_name(synth, cts)
    g.connect_by_name(synth, custom_flowgen_setup)

    g.connect_by_name(custom_flowgen_setup, iflow)
    g.connect_by_name(iflow, init)
    g.connect_by_name(iflow, power)
    g.connect_by_name(iflow, place)
    g.connect_by_name(iflow, cts)
    g.connect_by_name(iflow, postcts_hold)
    g.connect_by_name(iflow, route)
    g.connect_by_name(iflow, postroute)
    g.connect_by_name(iflow, signoff)

    g.connect_by_name(custom_init, init)
    g.connect_by_name(custom_power, power)

    # Fetch short-fix script in prep for eventual use by postroute
    g.connect_by_name(short_fix, postroute)

    g.connect_by_name(init, power)
    g.connect_by_name(power, place)
    g.connect_by_name(place, cts)
    g.connect_by_name(cts, postcts_hold)
    g.connect_by_name(postcts_hold, route)
    g.connect_by_name(route, postroute)
    g.connect_by_name(postroute, signoff)

    g.connect_by_name(signoff, drc)
    g.connect_by_name(signoff, lvs)
    g.connect(signoff.o('design-merged.gds'), drc.i('design_merged.gds'))
    g.connect(signoff.o('design-merged.gds'), lvs.i('design_merged.gds'))

    g.connect_by_name(signoff, genlibdb)
    g.connect_by_name(adk, genlibdb)
    g.connect_by_name(genlibdb_constraints, genlibdb)

    g.connect_by_name(genlibdb, lib2db)

    g.connect_by_name(adk, pt_signoff)
    g.connect_by_name(signoff, pt_signoff)

    g.connect_by_name(application, testbench)
    if synth_power:
        g.connect_by_name(application, post_synth_power)
        g.connect_by_name(synth, post_synth_power)
        g.connect_by_name(testbench, post_synth_power)

    g.connect_by_name(application, post_pnr_power)
    g.connect_by_name(signoff, post_pnr_power)
    g.connect_by_name(pt_signoff, post_pnr_power)
    g.connect_by_name(testbench, post_pnr_power)

    g.connect_by_name(adk, debugcalibre)
    g.connect_by_name(synth, debugcalibre)
    g.connect_by_name(iflow, debugcalibre)
    g.connect_by_name(signoff, debugcalibre)
    g.connect_by_name(drc, debugcalibre)
    g.connect_by_name(lvs, debugcalibre)

    # Pwr aware steps:
    if pwr_aware:
        g.connect_by_name(power_domains, synth)
        g.connect_by_name(power_domains, init)
        g.connect_by_name(power_domains, power)
        g.connect_by_name(power_domains, place)
        g.connect_by_name(power_domains, cts)
        g.connect_by_name(power_domains, postcts_hold)
        g.connect_by_name(power_domains, route)
        g.connect_by_name(power_domains, postroute)
        g.connect_by_name(power_domains, signoff)
        g.connect_by_name(adk, pwr_aware_gls)
        g.connect_by_name(signoff, pwr_aware_gls)
        # g.connect(power_domains.o('pd-globalnetconnect.tcl'), power.i('globalnetconnect.tcl'))

    # New 'custom_cts' step added for gf12
    if want_custom_cts:
        cts.extend_inputs(custom_cts.all_outputs())
        g.add_step(custom_cts)
        g.connect_by_name(custom_cts, cts)

    # New 'drc_pm' step, added for gf12
    if want_drc_pm:
        g.add_step(drc_pm)
        g.connect_by_name(adk, drc_pm)
        g.connect_by_name(signoff, drc_pm)
        g.connect(signoff.o('design-merged.gds'), drc_pm.i('design_merged.gds'))
        g.connect_by_name(drc_pm, debugcalibre)

    g.connect_by_name(iflow, genlibdb)

    # -----------------------------------------------------------------------
    # Parameterize
    # -----------------------------------------------------------------------

    g.update_params(parameters)

    # Add custom timing scripts

    for c_step in custom_timing_steps:
        order = c_step.get_param('order')
        order.append('report-special-timing.tcl')
        c_step.set_param('order', order)
        c_step.extend_postconditions([{'pytest': 'inputs/test_timing.py'}])

    # Update PWR_AWARE variable
    synth.update_params({'PWR_AWARE': parameters['PWR_AWARE']}, True)
    init.update_params({'PWR_AWARE': parameters['PWR_AWARE']}, True)
    power.update_params({'PWR_AWARE': parameters['PWR_AWARE']}, True)

    if pwr_aware:
        init.update_params({'flatten_effort': parameters['flatten_effort']}, True)
        pwr_aware_gls.update_params({'design_name': parameters['design_name']}, True)

        ASS = ["assert 'Clamping logic structure in the SBs and CBs is maintained' in File( 'mflowgen-run.log' )"]
        init.extend_postconditions(ASS)
        place.extend_postconditions(ASS)
        cts.extend_postconditions(ASS)
        postcts_hold.extend_postconditions(ASS)
        route.extend_postconditions(ASS)
        postroute.extend_postconditions(ASS)
        signoff.extend_postconditions(ASS)
    # Since we are adding an additional input script to the generic Innovus
    # steps, we modify the order parameter for that node which determines
    # which scripts get run and when they get run.

    init.update_params({'core_density_target': parameters['core_density_target']}, True)
    # init -- Add 'edge-blockages.tcl' after 'pin-assignments.tcl'
    # and 'additional-path-groups' after 'make_path_groups'

    order = init.get_param('order')  # get the default script run order
    path_group_idx = order.index('make-path-groups.tcl')
    order.insert(path_group_idx + 1, 'additional-path-groups.tcl')
    pin_idx = order.index('pin-assignments.tcl')  # find pin-assignments.tcl
    order.insert(pin_idx + 1, 'edge-blockages.tcl')  # add here
    init.update_params({'order': order})

    # Adding new input for genlibdb node to run

    # No longer conditional---amber and onyx now use same genlib mechanism
    order = genlibdb.get_param('order')  # get the default script run order
    extraction_idx = order.index('extract_model.tcl')  # find extract_model.tcl
    order.insert(extraction_idx, 'genlibdb-constraints.tcl')  # add here
    genlibdb.update_params({'order': order})

    # genlibdb -- Remove 'report-interface-timing.tcl' beacuse it takes
    # very long and is not necessary
    order = genlibdb.get_param('order')
    order.remove('write-interface-timing.tcl')
    genlibdb.update_params({'order': order})

    # Pwr aware steps:
    if pwr_aware:
        # init node
        order = init.get_param('order')
        read_idx = order.index('floorplan.tcl')  # find floorplan.tcl

        # 09/2022 reordered to load params (pe-pd-params) before using params (pe-load-upf)
        order.insert(read_idx + 1, 'pe-pd-params.tcl')                # add here
        order.insert(read_idx + 2, 'pe-load-upf.tcl')                 # add here
        order.insert(read_idx + 3, 'pd-aon-floorplan.tcl')            # add here
        order.insert(read_idx + 4, 'add-endcaps-welltaps-setup.tcl')  # add here
        order.insert(read_idx + 5, 'pd-add-endcaps-welltaps.tcl')     # add here
        order.insert(read_idx + 6, 'add-power-switches.tcl')          # add here
        order.remove('add-endcaps-welltaps.tcl')
        order.append('check-clamp-logic-structure.tcl')
        init.update_params({'order': order})

        # synth node (needs parm 'adk_allow_sdf_regs')
        order = synth.get_param('order')
        order.insert(0, 'pe-pd-params.tcl')        # add params file
        synth.update_params({'order': order})

        # power node
        order = power.get_param('order')
        order.insert(0, 'pd-globalnetconnect.tcl')  # add new 'pd-globalnetconnect'
        order.remove('globalnetconnect.tcl')        # remove old 'globalnetconnect'
        order.insert(0, 'pe-pd-params.tcl')         # add params file
        power.update_params({'order': order})

        # place node
        order = place.get_param('order')
        read_idx = order.index('main.tcl')  # find main.tcl
        order.insert(read_idx + 1, 'add-aon-tie-cells.tcl')
        order.insert(read_idx - 1, 'place-dont-use-constraints.tcl')
        order.append('check-clamp-logic-structure.tcl')
        place.update_params({'order': order})

        # cts node
        order = cts.get_param('order')
        order.insert(0, 'conn-aon-cells-vdd.tcl')  # add here
        order.append('check-clamp-logic-structure.tcl')
        cts.update_params({'order': order})

        # postcts_hold node
        order = postcts_hold.get_param('order')
        order.insert(0, 'conn-aon-cells-vdd.tcl')  # add here
        order.append('check-clamp-logic-structure.tcl')
        postcts_hold.update_params({'order': order})

        # route node
        order = route.get_param('order')
        order.insert(0, 'conn-aon-cells-vdd.tcl')  # add here
        order.append('check-clamp-logic-structure.tcl')
        route.update_params({'order': order})

        # postroute node
        order = postroute.get_param('order')
        order.insert(0, 'conn-aon-cells-vdd.tcl')  # add here
        order.append('check-clamp-logic-structure.tcl')
        postroute.update_params({'order': order})

        # Add fix-shorts as the last thing to do in postroute
        order = postroute.get_param('order')       # get the default script run order
        order.append('fix-shorts.tcl')             # Add fix-shorts at the end
        postroute.update_params({'order': order})  # Update

        # signoff node
        order = signoff.get_param('order')
        order.insert(0, 'conn-aon-cells-vdd.tcl')  # add here
        read_idx = order.index('generate-results.tcl')  # find generate_results.tcl
        order.insert(read_idx + 1, 'pd-generate-lvs-netlist.tcl')
        order.append('check-clamp-logic-structure.tcl')
        signoff.update_params({'order': order})

    return g


if __name__ == '__main__':
    g = construct()
    # g.plot()
