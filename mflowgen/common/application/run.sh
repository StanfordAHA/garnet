#!/bin/bash

# Build up the flags we want to pass to python garnet.v
flags="--width $array_width --height $array_height --pipeline_config_interval $pipeline_config_interval -v --interconnect-only"
map_flags="--width $array_width --height $array_height --pipeline_config_interval $pipeline_config_interval --interconnect-only"

if [ ${PWR_AWARE} = "False" ]; then
  flags="$flags --no-pd"
  map_flags="$map_flags --no-pd"
fi

# Clone AHA repo
git clone https://github.com/StanfordAHA/aha.git
cd aha
# install the aha wrapper script
pip install -e .

# Prune docker images...
yes | docker image prune -a --filter "until=6h" --filter=label='description=garnet' || true
docker container prune -f
# pull docker image from docker hub
docker pull stanfordaha/garnet:latest

# run the container in the background and delete it when it exits
# (this will print out the name of the container to attach to)
container_name=$(aha docker)
echo "container-name: $container_name"

docker exec $container_name /bin/bash -c "rm -rf /aha/garnet"
# Clone local garnet repo to prevent copying untracked files
git clone $GARNET_HOME ./garnet
docker cp ./garnet $container_name:/aha/garnet
# run the tests in the container and get all relevant files (tb, place file)
docker exec $container_name /bin/bash -c \
  "source /cad/modules/tcl/init/bash;
   module load xcelium;
   source /aha/bin/activate;
   aha garnet ${flags};
   cd garnet;
   aha halide ${app_to_run};
   aha map ${app_to_run} ${map_flags};
   aha test ${app_to_run};"
docker cp $container_name:/aha/garnet/temp/design.place ../design.place
docker cp $container_name:/aha/garnet/temp/design.route ../design.route
docker cp $container_name:/aha/garnet/temp/design.info ../design.info
docker cp $container_name:/aha/garnet/temp/design.packed ../design.packed
docker cp $container_name:/aha/garnet/temp/design.layout ../design.layout
docker cp $container_name:/aha/garnet/temp/1.graph ../1.graph
docker cp $container_name:/aha/garnet/temp/16.graph ../16.graph
docker cp $container_name:/aha/garnet/temp/garnet/waveforms.vcd ../outputs/run.vcd
grep '#m' ../design.place | awk '{printf "%s,%02X,%02X\n",$1,$2,$3}' > ../outputs/tiles_Tile_MemCore.list
grep '#p' ../design.place | awk '{printf "%s,%02X,%02X\n",$1,$2,$3}' > ../outputs/tiles_Tile_PE.list
# Kill the container
docker kill $container_name
echo "killed docker container $container_name"
cd $current_dir
