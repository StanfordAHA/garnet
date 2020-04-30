# =============================================================================
# construct.py
# =============================================================================
# Garnet SoC RTL Simulation
#
# Author    : Gedeon Nyengele
# Date      : April 5, 2020
# =============================================================================

import os
from mflowgen.components import Graph, Step


def construct():
    g = Graph()

    # -------------------------------------------------------------------------
    # Supported tests
    # -------------------------------------------------------------------------

    test_names = [
        # CPU Tests
        'apb_mux_test',
        'hello_test',
        'memory_test',
        'dma_single_channel',
        'default_slaves_test',
        'interrupts_test',
        'tlx_test',
        'cgra_test',

        # CXDT Tests
        'discovery',
    ]

    # -------------------------------------------------------------------------
    # Parameters
    # -------------------------------------------------------------------------

    parameters = {
        'construct_file': __file__,
        'design_name': 'test-soc',
        'soc_only'  : False,
        'interconnect_only' : False,
        'array_width': 8,
        'array_height': 4,
        'ARM_IP_DIR': '/sim/nyengele/aham3soc_armip',
        'AHA_IP_DIR': '/sim/nyengele/aham3soc',
        'GARNET_DIR': '/sim/nyengele/garnet',
        'TLX_FWD_DATA_LO_WIDTH': 16,
        'TLX_REV_DATA_LO_WIDTH': 45,
    }

    # -------------------------------------------------------------------------
    # Custom steps
    # -------------------------------------------------------------------------

    this_dir = os.path.dirname(os.path.abspath(__file__))

    garnet_rtl      = Step(this_dir + '/garnet_rtl')
    compile_design  = Step(this_dir + '/compile_design')
    build_test      = Step(this_dir + '/build_test')
    run_test        = Step(this_dir + '/run_test')
    verdict         = Step(this_dir + '/verdict')

    # -------------------------------------------------------------------------
    # Parallelize test build and run
    # -------------------------------------------------------------------------

    test_count = len(test_names)
    build_steps = list(map((lambda _: build_test.clone()), range(test_count)))
    run_steps = list(map((lambda _: run_test.clone()), range(test_count)))

    for step, name in zip(build_steps, test_names):
        step.set_name('build_' + name)
    for step, name in zip(run_steps, test_names):
        step.set_name('run_' + name)

    # -------------------------------------------------------------------------
    # Input/output dependencies
    # -------------------------------------------------------------------------

    # 'compile_design' step produces a simulation executable and its accompanying collateral
    compile_design.extend_outputs(['simv', 'simv.daidir'])
    compile_design.extend_inputs(['design.v'])

    # 'build_test' produces final images for both the CXDT and CPU
    for step in build_steps:
        step.extend_outputs(['CXDT.bin'])

    # 'run_tests' takes CXDT.bin, CPU.bin, and simv to produce a log
    for step, test in zip(run_steps, test_names):
        step.extend_inputs(['CXDT.bin', 'simv', 'simv.daidir'])
        step.extend_outputs(['vcs_run_' + test + '.log'])

    # 'verdict' consumes the run logs
    run_logs = list(map((lambda test: 'vcs_run_' + test + '.log'), test_names))
    verdict.extend_inputs(run_logs)

    # -------------------------------------------------------------------------
    # Graph -- Add nodes
    # -------------------------------------------------------------------------

    g.add_step(garnet_rtl)
    g.add_step(compile_design)

    for s in build_steps:
        g.add_step(s)

    for s in run_steps:
        g.add_step(s)

    g.add_step(verdict)

    # -------------------------------------------------------------------------
    # Graph -- Add edges
    # -------------------------------------------------------------------------

    g.connect_by_name(garnet_rtl, compile_design)

    for r, b in zip(run_steps, build_steps):
        g.connect_by_name(b, r)
        g.connect_by_name(compile_design, r)
        g.connect_by_name(r, verdict)

    # -------------------------------------------------------------------------
    # Set general parameters
    # -------------------------------------------------------------------------

    g.update_params(parameters)

    # -------------------------------------------------------------------------
    # Set node-specific parameters
    # -------------------------------------------------------------------------

    for step, test in zip(build_steps, test_names):
        step.update_params({'TEST_NAME': test})
    for step, test in zip(run_steps, test_names):
        step.update_params({'TEST_NAME': test})

    garnet_rtl.update_params({'GARNET_HOME': parameters['GARNET_DIR']})

    compile_design.update_params({'CGRA_RD_WS': 4})

    # -------------------------------------------------------------------------
    # Pre-conditions
    # -------------------------------------------------------------------------

    # 'verdict' requires all tests to have passed
    verdict.extend_preconditions(
        ["assert 'TEST PASSED' in File('inputs/" + run_log +
         "', enable_case_sensitive = True)" for run_log in run_logs]
    )

    # -------------------------------------------------------------------------
    # Post-conditions
    # -------------------------------------------------------------------------

    # 'compile_tbench' must be successful
    compile_design.extend_postconditions([
        "assert 'Error' not in File('vcs_compile.log', enable_case_sensitive = True)",
        "assert File('outputs/simv')",
        "assert File('outputs/simv.daidir')"
    ])

    return g


if __name__ == '__main__':
    g = construct()
