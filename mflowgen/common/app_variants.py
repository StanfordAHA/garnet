"""App-bundle variants in one tile graph: several recorded app runs replayed on
the SAME synthesized tile (e.g. two mappings of one app), so their power
differs only by activity, not by netlist.

env APP_BUNDLE_VARIANTS="A=/bundles/A/<config>,B=/bundles/B/<config>" adds, per
variant v, a copy of the app-replay chain with its own bundle:

  application-v -> testbench-v -> post-synth-power-v

wired like the tile graph's own application -> testbench -> post-synth-power
(post-synth-power-v also reads the graph's synth netlist, and the SRAM model
where the tile has one). `make post-synth-power-A post-synth-power-B` then
replays both on one synth. Unset (the default): no steps added, the graph is
unchanged. Driver: mflowgen/cgra_app_power.py.
"""
import os
import re

ENV = "APP_BUNDLE_VARIANTS"


def app_bundle_variants(env=None):
    """[(name, bundle dir)] in the order given; [] when unset."""
    text = (os.environ if env is None else env).get(ENV, "").strip()
    out = []
    for item in filter(None, (s.strip() for s in text.split(","))):
        name, sep, path = item.partition("=")
        if not sep or not re.fullmatch(r"[A-Za-z0-9_]+", name) or not path:
            raise ValueError(f"{ENV}: bad entry {item!r} (want NAME=/bundle/dir, NAME in [A-Za-z0-9_])")
        if name in (n for n, _ in out):
            raise ValueError(f"{ENV}: variant {name} given twice")
        out.append((name, path))
    return out


def add_app_variant_steps(g, custom_step, rtl, synth, sram_steps=(), build_glb=False):
    """Add each variant's application / testbench / post-synth-power steps to
    g and connect them. Returns [(name, bundle, application, post_synth_power)]
    for set_app_variant_params, called after the graph's update_params."""
    added = []
    for name, bundle in app_bundle_variants():
        application = custom_step('/../common/application')
        testbench = custom_step('/../common/testbench')
        power = custom_step('/../common/tile-post-synth-power')
        application.set_name(f'application-{name}')
        testbench.set_name(f'testbench-{name}')
        power.set_name(f'post-synth-power-{name}')
        if build_glb:
            application.set_param('build_glb', True)
        for step in (application, testbench, power):
            g.add_step(step)
        g.connect_by_name(application, testbench)
        g.connect(rtl.o('design.v'), application.i('design.v'))
        g.connect_by_name(application, power)
        for step in sram_steps:
            g.connect_by_name(step, power)
        g.connect_by_name(synth, power)
        g.connect_by_name(testbench, power)
        added.append((name, bundle, application, power))
    return added


def set_app_variant_params(added):
    """Point each variant's steps at its own bundle (the graph-wide
    update_params gave them APP_BUNDLE's)."""
    for _, bundle, application, power in added:
        application.set_param('app_bundle', bundle)
        power.set_param('app_bundle', bundle)
