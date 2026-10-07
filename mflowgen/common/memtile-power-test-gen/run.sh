#!/bin/bash
# Generate the idle/active power-test testbenches for this spec's MemCore tile.
# Same python environment as the rtl step (common/rtl/gen_rtl.sh): the aha
# docker container with this host's garnet + lake copied in and lake at
# origin/THESIS, or (use_container=False) the host python in $GARNET_HOME.
set -e

if [ -z "$lake_spec_config" ]; then
    echo "*** ERROR: memtile-power-test-gen needs a lake spec (lake_spec_config is empty)" >&2
    exit 1
fi
SPEC_HOST="$(readlink -f "$lake_spec_config" 2>/dev/null || echo "$lake_spec_config")"
[ -f "$SPEC_HOST" ] || { echo "*** ERROR: lake_spec_config not found: $lake_spec_config" >&2; exit 1; }
MODE="${lake_spec_mode:-static}"
STEP_DIR="$(pwd)"
mkdir -p outputs

# garnet.py flags exactly as gen_rtl.sh builds them (minus -v: no verilog).
flags="--width $array_width --height $array_height"
flags+=" --pipeline_config_interval $pipeline_config_interval"
flags+=" --glb_tile_mem_size $glb_tile_mem_size"
[ "$PWR_AWARE" == False ] && flags+=" --no-pd"
flags+=" --use-non-split-fifos"
[ "$dual_port"    == True ] && flags+=" --dual-port"
[ "$use_sim_sram" == True ] && flags+=" --use_sim_sram"

gen_args="--sim-cycles $sim_cycles --clock-period $clock_period --seed $seed"

if [ "$use_container" == True ]; then
    image="$rtl_docker_image"
    if [ "$image" == "" -o "$image" == "default" ]; then image="stanfordaha/garnet:latest"; fi
    container_name=memtile_power_$$
    docker pull "$image"
    docker run -id --name $container_name --rm -v /cad:/cad "$image" bash
    trap "docker kill $container_name" EXIT
    docker exec $container_name /bin/bash -c 'source /aha/aha/bin/docker-bashrc; wait'

    if [ "$use_local_garnet" == True ]; then
        host_garnet="${GARNET_HOME:?GARNET_HOME must be set}"
        host_lake="${LAKE_PATH:-$(dirname "$host_garnet")/lake}"
        docker exec $container_name /bin/bash -c "rm -rf /aha/garnet /aha/lake"
        docker cp "$host_garnet" $container_name:/aha/garnet
        docker cp "$host_lake" $container_name:/aha/lake
    fi
    W=/tmp/memtile_power
    docker exec $container_name /bin/bash -c "mkdir -p $W/out"
    docker cp "$SPEC_HOST" $container_name:$W/spec_config.json
    docker cp "$(readlink -f inputs/design.v)" $container_name:$W/design.v
    # Ship the generator itself so a container garnet without it still works.
    docker cp gen_memtile_power_tests.py $container_name:$W/gen_memtile_power_tests.py

    # Same lake as the rtl step: THESIS tip (gen_rtl.sh checks it out the same
    # way). Inside a host double-quoted string: no double quotes, backticks or
    # dollar signs in comments here.
    docker exec $container_name /bin/bash -c "
        set -e
        source /aha/bin/activate
        git config --global --add safe.directory /aha/garnet
        git config --global --add safe.directory /aha/lake
        ( cd /aha/lake && git fetch origin THESIS && git checkout -B THESIS origin/THESIS && git log -1 --oneline )
        cd /aha/garnet
        export LAKE_SPEC_CONFIG=$W/spec_config.json LAKE_SPEC_MODE=$MODE USE_NON_SPLIT_FIFOS=True
        for try in 1 2 3; do
            if python $W/gen_memtile_power_tests.py --outdir $W/out --design-v $W/design.v $gen_args \
                 -- $flags --lake-spec-config $W/spec_config.json --lake-spec-mode $MODE; then
                exit 0
            fi
            echo '--- memtile-power-test-gen: attempt failed (garnet build is flaky: SIGSEGV/SIGABRT), retrying'
        done
        exit 1
    "
    docker cp $container_name:$W/out/. outputs/
    docker kill $container_name || true
    trap - EXIT
else
    cd "${GARNET_HOME:?GARNET_HOME must be set}"
    export LAKE_SPEC_CONFIG="$SPEC_HOST" LAKE_SPEC_MODE="$MODE" USE_NON_SPLIT_FIFOS=True
    ok=0
    for try in 1 2 3; do
        if python "$STEP_DIR/gen_memtile_power_tests.py" --outdir "$STEP_DIR/outputs" \
             --design-v "$(readlink -f "$STEP_DIR/inputs/design.v")" $gen_args \
             -- $flags --lake-spec-config "$SPEC_HOST" --lake-spec-mode $MODE; then
            ok=1; break
        fi
        echo "--- memtile-power-test-gen: attempt $try failed, retrying"
    done
    cd "$STEP_DIR"
    [ $ok == 1 ] || exit 1
fi
