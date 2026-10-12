"""Check that an app bundle was recorded on the CGRA this build is for.

  python3 check_bundle.py <bundle>/manifest.json [--spec SPEC_JSON] [--mode MODE]
                          [--design-v DESIGN_V --design-name Tile_MemCore|Tile_PE]

The bundle's run.vcd only replays correctly into a tile built like the one it
was recorded on. Fails (exit 1, every problem listed) unless:

  --spec/--mode   the bundle's lake spec + runtime mode (static / rv) equal this
                  build's (an empty --spec = default onyx MemCore, which a
                  lake-spec bundle does not match). Skipped when not given.
  --design-v      this build's RTL (the rtl step's design.v) has the tile module
                  --design-name with exactly the ports the bundle recorded
                  (tile_ports.json), and the tile's lake core is the same
                  module with the same ports: Tile_MemCore's controller
                  (core_ports.json), Tile_PE's pond (the bundle's garnet.v.gz;
                  an RV-mode CGRA has the RV spec pond, which the Tile_PE graph
                  does not build, so Tile_PE takes a static bundle). Spec + mode cannot
                  see a changed controller: lake 144e2062 pruned the RV
                  comparators of the SAME spec, which shrank config_memory
                  (1421 bits for fw4 sc8192 rv), and a bundle recorded before it
                  replayed config writes into the wrong bits without an error.
"""
import argparse
import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_app_bundle import CORE_MODULE_RE, find_instance_path, module_ports, verilog_modules  # noqa: E402

# lake build_spec's defaults: a spec JSON may leave any of them out (the
# sweep's configs carry vec_capacity, a hand-written spec often doesn't).
# Same table as sweep_specs.SPEC_DEFAULTS.
SPEC_DEFAULTS = dict(storage_capacity=4096, data_width=16, vec_width=4, dims=6,
                     in_ports=2, out_ports=2, dual_port=False, vec_capacity=2,
                     max_extent=None, max_sequence_width=None)
MAX_LISTED = 8
# The lake-generated core of each tile (outermost match under the tile):
# MEM controller (static / RV spec) and PE pond (legacy PondTop, spec pond).
LAKE_CORES = {"Tile_MemCore": CORE_MODULE_RE,
              "Tile_PE": re.compile(r"^(PondTop|lakespec_pond)(_W|_flat)?$")}
CORE_NAMES = {"Tile_MemCore": "lake controller", "Tile_PE": "pond"}


def norm(spec):
    return dict(SPEC_DEFAULTS, **(spec or {}))


def port_diff(what, recorded, built):
    """Problems between two module_ports() dicts, compared as {name: width}
    per direction (garnet.v port order is not run-to-run stable)."""
    problems = []
    for d in ("inputs", "outputs"):
        r, b = dict(map(tuple, recorded.get(d, []))), dict(map(tuple, built.get(d, [])))
        for kind, names in (("missing in this build", sorted(set(r) - set(b))),
                            ("not in the bundle", sorted(set(b) - set(r)))):
            if names:
                more = f" (+{len(names) - MAX_LISTED} more)" if len(names) > MAX_LISTED else ""
                problems.append(f"{what} {d} {kind}: {', '.join(names[:MAX_LISTED])}{more}")
        widths = [f"{n} {r[n]} -> {b[n]}" for n in sorted(set(r) & set(b)) if r[n] != b[n]]
        if widths:
            problems.append(f"{what} {d} width changed: {', '.join(widths[:MAX_LISTED])}")
    return problems


def check_spec(manifest, spec_path, mode):
    problems = []
    bundle_spec = manifest.get("spec_config")
    if spec_path:
        spec = json.load(open(spec_path))
        if norm(bundle_spec) != norm(spec):
            problems.append(f"spec {bundle_spec} != this build's {spec} ({spec_path})")
    elif bundle_spec:
        problems.append(f"bundle is for lake spec {bundle_spec}, this build has no lake_spec_config")
    if (mode or "static") != (manifest.get("mode") or "static"):
        problems.append(f"mode {manifest.get('mode')} != this build's {mode or 'static'}")
    return problems


def recorded_core(bundle_dir, design, bundle_mods):
    """(module, ports) of the tile's lake core the bundle was recorded on:
    core_ports.json (MEM controller), else the bundle's own garnet.v.gz;
    (None, None) when neither has one."""
    core_json = os.path.join(bundle_dir, "core_ports.json")
    if design == "Tile_MemCore" and os.path.isfile(core_json):
        core = json.load(open(core_json))
        return core.get("module"), core
    if bundle_mods is not None:
        _, mod = find_instance_path(bundle_mods, design, LAKE_CORES[design])
        if mod is not None:
            return mod, module_ports(bundle_mods[mod][0])
    return None, None


def check_rtl(bundle_dir, design_v, design):
    """Problems between the bundle's recorded tile (+ its lake core: MEM
    controller / PE pond) and this build's RTL."""
    mods = verilog_modules(open(design_v, errors="replace").read())
    if design not in mods:
        return [f"{design_v} has no module {design}"]
    tile_ports = json.load(open(os.path.join(bundle_dir, "tile_ports.json")))
    if design not in tile_ports:
        return [f"bundle tile_ports.json has no {design} (recorded designs: {sorted(tile_ports)})"]
    problems = port_diff(f"{design} ports:", tile_ports[design], module_ports(mods[design][0]))
    if design not in LAKE_CORES:
        return problems
    gz = os.path.join(bundle_dir, "garnet.v.gz")
    bundle_mods = verilog_modules(gzip.open(gz, "rt", errors="replace").read()) if os.path.isfile(gz) else None
    rec_mod, rec_ports = recorded_core(bundle_dir, design, bundle_mods)
    _, mod = find_instance_path(mods, design, LAKE_CORES[design])
    what = CORE_NAMES[design]
    if rec_mod is None and bundle_mods is None:
        print(f"WARNING: bundle has no core_ports.json / garnet.v.gz: {what} not checked", file=sys.stderr)
    elif rec_mod != mod:
        hint = (" (an RV-mode CGRA's PE tile has the RV spec pond; the Tile_PE graph builds the"
                " default pond: use a static bundle for Tile_PE)") if design == "Tile_PE" else ""
        problems.append(f"{what} module {mod} != the bundle's {rec_mod}{hint}")
    elif mod is not None:
        problems += port_diff(f"{what} {mod} ports:", rec_ports, module_ports(mods[mod][0]))
    return problems


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("manifest")
    p.add_argument("--spec", default=None, help="this build's lake_spec_config ('' = none)")
    p.add_argument("--mode", default=None, help="this build's lake_spec_mode")
    p.add_argument("--design-v", default=None, help="this build's RTL (rtl step design.v)")
    p.add_argument("--design-name", default=None, help="tile module to compare (Tile_MemCore / Tile_PE)")
    args = p.parse_args(argv)

    manifest = json.load(open(args.manifest))
    bundle_dir = os.path.dirname(os.path.abspath(args.manifest))
    problems, checked = [], []
    if args.spec is not None or args.mode is not None:
        problems += check_spec(manifest, args.spec, args.mode)
        checked.append("spec+mode")
    if args.design_v:
        if not args.design_name:
            p.error("--design-v needs --design-name")
        problems += check_rtl(bundle_dir, args.design_v, args.design_name)
        checked.append(f"{args.design_name} ports vs {args.design_v}")

    if problems:
        print(f"*** ERROR: app bundle {args.manifest} does not match this build "
              f"(regenerate it with gen_app_bundle.py on this garnet + lake):\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    print(f"app bundle OK ({', '.join(checked) or 'nothing checked'}): app {manifest.get('app')}, "
          f"mode {manifest.get('mode')}, {manifest.get('width')}x{manifest.get('height')} CGRA, "
          f"garnet.v md5 {manifest.get('garnet_v_md5')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
