"""Check that an app bundle was recorded on the CGRA this build is for.

  python3 check_bundle.py <bundle>/manifest.json <lake_spec_config or ""> <lake_spec_mode or "">

The bundle's run.vcd only replays correctly into a tile built from the same
lake spec in the same runtime mode (static / rv): its config writes and port
traffic are that MemCore's. Fails on a mismatch; with no lake_spec_config
(default onyx MemCore) a lake-spec bundle is a mismatch too.
"""
import json
import sys

# lake build_spec's defaults: a spec JSON may leave any of them out (the
# sweep's configs carry vec_capacity, a hand-written spec often doesn't).
# Same table as sweep_specs.SPEC_DEFAULTS.
SPEC_DEFAULTS = dict(storage_capacity=4096, data_width=16, vec_width=4, dims=6,
                     in_ports=2, out_ports=2, dual_port=False, vec_capacity=2,
                     max_extent=None, max_sequence_width=None)


def norm(spec):
    return dict(SPEC_DEFAULTS, **(spec or {}))


manifest_path, spec_path, mode = sys.argv[1], sys.argv[2], sys.argv[3]
manifest = json.load(open(manifest_path))
bundle_spec = manifest.get("spec_config")
bundle_mode = manifest.get("mode")
problems = []

if spec_path:
    spec = json.load(open(spec_path))
    if norm(bundle_spec) != norm(spec):
        problems.append(f"spec {bundle_spec} != this build's {spec} ({spec_path})")
elif bundle_spec:
    problems.append(f"bundle is for lake spec {bundle_spec}, this build has no lake_spec_config")
if (mode or "static") != (bundle_mode or "static"):
    problems.append(f"mode {bundle_mode} != this build's {mode or 'static'}")

if problems:
    sys.exit("*** ERROR: app bundle " + manifest_path + " does not match this build:\n  " + "\n  ".join(problems))
print(f"app bundle OK: app {manifest.get('app')}, mode {bundle_mode}, "
      f"{manifest.get('width')}x{manifest.get('height')} CGRA, garnet.v md5 {manifest.get('garnet_v_md5')}")
