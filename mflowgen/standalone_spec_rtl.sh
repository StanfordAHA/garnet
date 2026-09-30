#!/bin/bash
# Generate STANDALONE lake-spec RTL (lake tests/test_spec/thesis_sweep.py) in
# the same aha docker image + lake THESIS checkout that common/rtl/gen_rtl.sh
# uses for the tile, so the standalone and tile RTL come from identical lake /
# kratos code and the host needs no lake Python stack.
#
# Opt-in (sweep_specs.py --standalone-rtl container); not yet exercised on a
# machine with docker. Called by lake's pd/thesis `rtl` step (via the
# python_command graph kwarg sweep_specs.py sets), from inside that step dir:
#
#   standalone_spec_rtl.sh <host_outdir> <thesis_sweep.py args...>
#
# Leaves <host_outdir>/{inputs/lakespec.sv,tb.sv,gold,...} exactly as a host
# `thesis_sweep.py --outdir <host_outdir>` would.
#
# Env: LAKE_PATH        host lake checkout to copy in (required)
#      RTL_DOCKER_IMAGE image (default stanfordaha/garnet:latest, as gen_rtl)

set -euo pipefail

host_outdir=${1:?usage: $0 <host_outdir> <thesis_sweep args...>}
shift
host_lake=${LAKE_PATH:?LAKE_PATH must point at the host lake checkout}
image=${RTL_DOCKER_IMAGE:-stanfordaha/garnet:latest}
ctr_outdir=/tmp/lakespec_standalone
sweep_args=$(printf ' %q' "$@")

# gen_rtl pulls on every tile build; only pull here when the image is missing
# so a sweep's standalone runs use the same image its tile builds just did.
docker image inspect "$image" > /dev/null 2>&1 || docker pull "$image"

container_name=standalone_rtl_$$
echo "--- standalone_spec_rtl: container $container_name ($image)"
docker run -id --name "$container_name" --rm -v /cad:/cad "$image" bash > /dev/null
trap 'docker kill "$container_name" > /dev/null 2>&1 || true' EXIT
docker exec "$container_name" /bin/bash -c 'source /aha/aha/bin/docker-bashrc; wait'

echo "--- standalone_spec_rtl: copying in $host_lake"
docker exec "$container_name" rm -rf /aha/lake
docker cp "$host_lake" "$container_name":/aha/lake

# Same lake revision rule as gen_rtl.sh: track origin/THESIS tip.
docker exec "$container_name" /bin/bash -c "
  set -e
  source /aha/bin/activate
  git config --global --add safe.directory /aha/lake
  cd /aha/lake
  git fetch origin THESIS
  git checkout -B THESIS origin/THESIS
  git log -1 --oneline
  python tests/test_spec/thesis_sweep.py $sweep_args --outdir $ctr_outdir
"

rm -rf "$host_outdir"
mkdir -p "$(dirname "$host_outdir")"
docker cp "$container_name":"$ctr_outdir" "$host_outdir"
echo "--- standalone_spec_rtl: RTL in $host_outdir"
